import socket
import threading
import logging

from server.client_session import ClientSession


class TCPServer:
    def __init__(self, ip, port):
        self.logger = logging.getLogger('TCPServer')
        self.logger.setLevel(logging.DEBUG)
        logging.basicConfig(format='%(asctime)s - %(message)s')
        self.logger.info(f"Server is listening on {ip}:{port}")

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((ip, port))
        self.server_socket.listen(5)

    def accept_connections(self):
        while True:
            try:
                client_socket, addr = self.server_socket.accept()
                self.logger.info(f"Connection accepted from {addr}")
                client_session = ClientSession(client_socket, addr)
                threading.Thread(target=client_session.manage_playback).start()
                threading.Thread(target=client_session.process_commands).start()
            except Exception as e:
                self.logger.error(f"Error accepting connections: {e}")
                break

    def close_server(self):
        self.server_socket.close()
        self.logger.info("Server shutdown successfully.")
