import threading
import cv2
import queue

class WebcamCapture():
    def __init__(self):
        super().__init__()
        self.stop_capturing = threading.Event()  # Event flag to stop the capture thread
        self.capture_thread = None
        self.frame_queue = queue.Queue()  # Queue to store the frames
        self.video_writer = None  # This will be used to write frames to a video file

    def start_capture(self, save_file_path=None, fps=20.0, resolution=(640, 480)):
        """Start capturing frames from the webcam."""
        # Setup video writer if save path is provided
        if save_file_path:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            self.video_writer = cv2.VideoWriter(save_file_path, fourcc, fps, resolution)
        
        self.stop_capturing.clear()
        if self.capture_thread is None or not self.capture_thread.is_alive():
            self.capture_thread = threading.Thread(target=self._read_frames)
            self.capture_thread.start()

    def _read_frames(self):
        """Read frames from the webcam and put them into the queue."""
        capture_device = cv2.VideoCapture(0)  # Open default camera
        if not capture_device.isOpened():
            print("Error: Could not open video source.")
            return

        try:
            while not self.stop_capturing.is_set():
                ok, frame = capture_device.read()
                if ok:
                    self.frame_queue.put(frame)
                    if self.video_writer:
                        self.video_writer.write(frame)  # Write frame to video file
        finally:
            capture_device.release()    # Release the capture device
            if self.video_writer:
                self.video_writer.release()  # Release the video writer and save the video file

    def get_frame(self):
        """Retrieve a frame from the queue."""
        return self.frame_queue.get() if not self.frame_queue.empty() else None

    def stop_capture(self):
        self.stop_capturing.set()
        if self.capture_thread and self.capture_thread.is_alive():
            self.capture_thread.join()
        self.capture_thread = None