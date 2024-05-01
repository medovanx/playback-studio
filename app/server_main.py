from server.tcp_server import TCPServer

if __name__ == "__main__":
    server = TCPServer('localhost', 5000)
    server.accept_connections()