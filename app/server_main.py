from server.tcp_server import TCPServer

if __name__ == "__main__":
    server = TCPServer('26.198.75.248', 5000)
    server.accept_connections()