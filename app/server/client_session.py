import struct
import cv2
from queue import Queue
import threading
import logging

class ClientSession:
    def __init__(self, socket, address):
        self.socket = socket
        self.address = address
        self.video_path = r'M:\Mohamed\Programming\Playback Studio\app\data\boo.mp4'
        self.is_playing = False
        self.capture = None
        self.command_queue = Queue()
        self.lock = threading.Lock()  # Create a lock for thread-safe operations on the video capture object

    def send_frame(self, frame):
        try:
            _, buffer = cv2.imencode('.jpg', frame)
            data = buffer.tobytes()
            message = struct.pack(">L", len(data)) + data
            self.socket.sendall(message)
            print(f"Sent frame of size {len(data)}")  # Debugging line
        except Exception as e:
            logging.error(f"Failed to send frame: {e}")

    def manage_playback(self):
        self.capture = cv2.VideoCapture(self.video_path)
        while True:
            with self.lock:  # Acquire lock before accessing the capture object
                if not self.is_playing: # Check if playback is paused, then wait for a command
                    command = self.command_queue.get()
                    if command == "stop":
                        break
                    continue

                ret, frame = self.capture.read()
                if not ret:
                    break  # End of video
                self.send_frame(frame)

        self.capture.release()

    def process_commands(self):
        while True:
            try:
                data = self.socket.recv(1024)
                print(f"Data received: {data}")  # Check raw data received
                if not data:
                    break
                command = data.decode().strip().lower()
                print(f"Processed command: {command}")  # Debugging line
                if command in ["play", "pause"]:
                    self.is_playing = (command == "play")
                    self.command_queue.put(command)  # Ensure all commands are put in the queue
                elif command == "rewind":
                    self.rewind_video()  
                elif command.startswith("seek"):
                    _, position = command.split()
                    self.seek_video(int(position))
            except Exception as e:
                logging.error(f"Error processing commands from {self.address}: {e}")
                break

    def rewind_video(self, rewind_time=5000):  # Default rewind time is 5 seconds
        """Rewind the video by a certain amount of time in milliseconds."""
        with self.lock:  # Use the lock to ensure thread-safe access
            if self.capture:
                # Get current position in milliseconds
                current_position = self.capture.get(cv2.CAP_PROP_POS_MSEC)
                # Calculate new position
                new_position = max(0, current_position - rewind_time)  # Ensure new position is not negative
                # Set the new position
                self.capture.set(cv2.CAP_PROP_POS_MSEC, new_position)


    def seek_video(self, position):
        with self.lock:  # Use the lock to ensure thread-safe access
            if self.capture:
                total_duration = self.capture.get(cv2.CAP_PROP_POS_MSEC)
                if position >= 0 and position <= total_duration:
                    self.capture.set(cv2.CAP_PROP_POS_MSEC, position)
                else:
                    logging.warning("Invalid seek position")
