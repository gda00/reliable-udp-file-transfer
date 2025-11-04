import socket
import os
import struct
import zlib
import threading

HOST = "0.0.0.0"
PORT = 1025

BUFFER_SIZE = 1024
HEADER_FORMAT = '!IIB'
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)
PAYLOAD_SIZE = BUFFER_SIZE - HEADER_SIZE

FLAG_DATA = 0
FLAG_FIN = 1
FLAG_ACK = 2

def handle_client_request(request, client_address):
    worker_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    try:
        print(f"[Thread-{threading.get_ident()}] Iniciando atendimento para {client_address}")
        request_str = request.decode('utf-8')
        print(f"[Thread-{threading.get_ident()}] {request_str}")
        
        parts = request_str.split()
        if len(parts) == 2 and parts[0] == "GET":
            filename = parts[1]

            if os.path.exists(filename):
                print(f"[Thread-{threading.get_ident()}] Enviando o arquivo: {filename} para {client_address}")
                sequence_number = 0
                with open(filename, 'rb') as f:
                    while True:
                        chunk = f.read(PAYLOAD_SIZE)

                        if not chunk:
                            fin_header = struct.pack(HEADER_FORMAT, sequence_number, 0, FLAG_FIN)
                            while True:
                                worker_socket.sendto(fin_header, client_address)
                                worker_socket.settimeout(1.0)
                                try:
                                    ack_packet, addr = worker_socket.recvfrom(BUFFER_SIZE)
                                    ack_header = ack_packet[:HEADER_SIZE]
                                    ack_seq, _, ack_flags = struct.unpack(HEADER_FORMAT, ack_header)
                                    if addr == client_address and ack_flags == FLAG_ACK and ack_seq == sequence_number:
                                        print(f"[Thread-{threading.get_ident()}] ACK para FIN SEQ={sequence_number} recebido.")
                                        break
                                except socket.timeout:
                                    print(f"[Thread-{threading.get_ident()}] Timeout! Retransmitindo pacote FIN SEQ={sequence_number}...")
                            break
                        
                        checksum = zlib.crc32(chunk)
                        header = struct.pack(HEADER_FORMAT, sequence_number, checksum, FLAG_DATA)
                        packet = header + chunk
                        
                        while True:
                            worker_socket.sendto(packet, client_address)
                            worker_socket.settimeout(1.0)
                            try:
                                ack_packet, addr = worker_socket.recvfrom(BUFFER_SIZE)
                                ack_header = ack_packet[:HEADER_SIZE]
                                ack_seq, _, ack_flags = struct.unpack(HEADER_FORMAT, ack_header)
                                if addr == client_address and ack_flags == FLAG_ACK and ack_seq == sequence_number:
                                    break
                            except socket.timeout:
                                print(f"[Thread-{threading.get_ident()}] Timeout! Retransmitindo pacote DATA SEQ={sequence_number}...")
                        
                        sequence_number += 1

                print(f"[Thread-{threading.get_ident()}] Arquivo {filename} enviado com sucesso.")
            else:
                print(f"[Thread-{threading.get_ident()}] Arquivo {filename} nao encontrado.")
                error_msg = b'ERROR: File not found'
                worker_socket.sendto(error_msg, client_address)
    except Exception as e:
        print(f"[Thread-{threading.get_ident()}] Erro durante o atendimento de {client_address}: {e}")
    finally:
        print(f"[Thread-{threading.get_ident()}] Finalizando e fechando socket para {client_address}")
        worker_socket.close()

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((HOST, PORT))
    print(f"Servidor UDP principal escutando em {HOST}:{PORT}")
    
    try:
        while True:
            try:
                request, client_address = server_socket.recvfrom(BUFFER_SIZE)
                print(f"\nNova requisição de {client_address}. Criando uma thread para o atendimento.")
                
                client_handler_thread = threading.Thread(target=handle_client_request, args=(request, client_address))
                client_handler_thread.start()
            except Exception as e:
                print(f"Erro no loop principal do servidor: {e}")
    except KeyboardInterrupt:
        print("\nServidor sendo desligado...")
    finally:
        print("Fechando o socket do servidor.")
        server_socket.close()
main()