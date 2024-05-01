import cv2
import numpy as np
import socket
import struct

from PyQt5.QtCore import pyqtSignal, QObject


class TCPClient(QObject):
    frame_ready = pyqtSignal(np.ndarray)  # Emit frame as ndarray for further processing

    def __init__(self, server_port):
        super().__init__()
        self.server_port = server_port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect_to_server(self, host):
        try:
            self.socket.connect((host, self.server_port))
            print(f"Connected to server at {host}:{self.server_port}")
        except Exception as e:
            print(f"Failed to connect to server: {e}")
            return False
        return True

    def receive_video_stream(self):
        try:
            while True:
                # Receive the size of the frame first
                frame_size_data = self.socket.recv(4)
                if len(frame_size_data) < 4:    # If no data is received, then continue
                    continue 
                frame_size = struct.unpack(">L", frame_size_data)[0]
                frame_data = b""

                # Receive the entire frame based on its size
                while len(frame_data) < frame_size:
                    packet = self.socket.recv(frame_size - len(frame_data))
                    if not packet:
                        return
                    frame_data += packet

                # Decode the image frame
                frame = np.frombuffer(frame_data, dtype=np.uint8)
                frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)

                if frame is not None:
                    self.frame_ready.emit(frame)
        except Exception as e:
            print(f"Socket operation failed: {e}")
        finally:
            self.close_connection()

    def send_command(self, command):
        try:
            self.socket.sendall(command.encode())
        except Exception as e:
            print(f"Failed to send command {command}: {e}")

    def close_connection(self):
        try:
            if self.socket:
                self.socket.shutdown(socket.SHUT_RDWR)
                self.socket.close()
                print("Socket closed.")
        except Exception as e:
            print(f"Error closing socket: {e}")

