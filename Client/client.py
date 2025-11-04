import socket
import os
import struct
import zlib
import random
import sys

BUFFER_SIZE = 1024
HEADER_FORMAT = '!IIB'
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)
LOSS_RATE = 0.20

FLAG_DATA = 0
FLAG_FIN = 1
FLAG_ACK = 2

print("Cliente UDP para Transferência de Arquivos")
user_input = input("Digite sua requisição no formato: @IP:PORTA/arquivo.txt: ")

try:
    user_input = user_input.split('@',1)[1]
    address_part, filename = user_input.split('/', 1)
    HOST, PORT_STR = address_part.split(':', 1)
    PORT = int(PORT_STR)
    if PORT <= 0 or PORT > 65535:
        raise ValueError("Porta inválida.")
    
except ValueError as e:
    print(f"Erro: {e}")
    sys.exit(1)

simulate_loss_input = input("Deseja simular perda de pacotes (s/n)? ").lower()
simulate_loss = True if simulate_loss_input == 's' else False

if simulate_loss:
    print(f"AVISO: Simulação de perda de pacotes ativada com uma taxa de {int(LOSS_RATE * 100)}%.")

server_address = (HOST, PORT)
request = f"GET {filename}"

client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
expected_sequence_number = 0

try:
    client_socket.settimeout(10.0)
    client_socket.sendto(request.encode('utf-8'), server_address)

    first_packet, server_info = client_socket.recvfrom(BUFFER_SIZE)

    if first_packet.startswith(b'ERROR:'):
        print(f"{first_packet.decode('utf-8')}")
    else:
        header_data = first_packet[:HEADER_SIZE]
        chunk = first_packet[HEADER_SIZE:]
        sequence_number, checksum, flags = struct.unpack(HEADER_FORMAT, header_data)
        
        if simulate_loss and random.random() < LOSS_RATE:
            print("--- SIMULANDO PERDA do primeiro pacote (SEQ=0) ---")
            raise socket.timeout("Simulação de perda do primeiro pacote")

        calculated_checksum = zlib.crc32(chunk)
        if sequence_number == 0 and checksum == calculated_checksum:
            print("Conexão estabelecida. Recebendo arquivo...")
            
            with open(filename, 'wb') as f:
                f.write(chunk)
                ack_header = struct.pack(HEADER_FORMAT, sequence_number, 0, FLAG_ACK)
                client_socket.sendto(ack_header, server_info)
                expected_sequence_number = 1
                
                while True:
                    packet, server_info = client_socket.recvfrom(BUFFER_SIZE)
                    
                    header_data = packet[:HEADER_SIZE]
                    chunk = packet[HEADER_SIZE:]
                    sequence_number, checksum, flags = struct.unpack(HEADER_FORMAT, header_data)
                    
                    if simulate_loss and random.random() < LOSS_RATE:
                        print(f"--- SIMULANDO PERDA do pacote SEQ={sequence_number} ---")
                        continue

                    calculated_checksum = zlib.crc32(chunk)
                    if checksum != calculated_checksum:
                        print(f"Checksum inválido para o pacote SEQ={sequence_number}. Descartado.")
                        continue
                    
                    if sequence_number == expected_sequence_number:
                        ack_header = struct.pack(HEADER_FORMAT, sequence_number, 0, FLAG_ACK)
                        client_socket.sendto(ack_header, server_info)
                        
                        if flags == FLAG_FIN:
                            print("Pacote FIN recebido. Transferência concluída.")
                            break
                        
                        f.write(chunk)
                        expected_sequence_number += 1
                    
                    elif sequence_number < expected_sequence_number:
                        print(f"Pacote duplicado SEQ={sequence_number} recebido. Reenviando ACK.")
                        ack_header = struct.pack(HEADER_FORMAT, sequence_number, 0, FLAG_ACK)
                        client_socket.sendto(ack_header, server_info)
        else:
            print("Erro: Primeiro pacote recebido é inválido. Abortando.")
except ConnectionResetError:
    print("\nErro: A conexão foi ativamente recusada pelo servidor.")
except socket.timeout:
    print("Erro: O servidor não respondeu ou o pacote inicial foi perdido. A transferência falhou.")
    if os.path.exists(filename):
        try:
            os.remove(filename)
            print("Arquivo parcial removido.")
        except OSError as e:
            print(f"Erro ao remover arquivo parcial: {e}")

finally:
    client_socket.close()