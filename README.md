# Reliable UDP File Transfer
A simple CLI client-server implementation of a reliable file transfer protocol over UDP.

## About The Project

This project builds a reliable data transfer protocol from scratch on top of the unreliable UDP protocol using Python sockets. It implements the Stop-and-Wait ARQ mechanism to ensure data integrity and ordered delivery, making it capable of transferring large files without corruption or loss.

The server is concurrent and uses Python's `threading` library to handle multiple clients simultaneously, giving each client its own isolated communication socket.

## Core Features

* **Reliable Delivery:** Implements the Stop-and-Wait ARQ protocol with packet timeouts and retransmissions.
* **Data Integrity:** Uses CRC32 checksums to validate each packet and discard corrupted data.
* **Ordered Delivery:** Guarantees in-order file assembly using packet sequence numbers.
* **Concurrent Server:** Utilizes multithreading to manage multiple simultaneous client downloads.
* **Reliable Teardown:** Implements a two-way `FIN`/`ACK` handshake to ensure connections are closed cleanly.
* **Error Simulation:** Includes an optional client-side packet loss simulation to test the protocol's robustness.
