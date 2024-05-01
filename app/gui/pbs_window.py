import os

from PyQt5.QtCore import pyqtSignal, QThread, pyqtSlot, Qt
from PyQt5.QtWidgets import QWidget, QFileDialog
from PyQt5.QtMultimedia import QMediaPlayer
from PyQt5.QtGui import QPixmap
from PyQt5 import uic, QtGui

import numpy as np

from recording.webcam_capture import WebcamCapture
from playback.video_playback import VideoPlayback
from shared.helpers import process_frame, convert_time_to_milliseconds
from live.tcp_client import TCPClient

gui_path = os.path.join(os.path.abspath("."), "app", "assets", "pbs_gui.ui")
Ui_MainWindow, QtBaseClass = uic.loadUiType(gui_path)


class PlaybackStudio(QWidget, Ui_MainWindow):
    # Signal to send the processed frame back to the GUI
    webcam_frame_ready = pyqtSignal(QPixmap)

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        icon_path = os.path.join(os.path.abspath("."), "app", "assets", "icon.png")
        self.setWindowIcon(QtGui.QIcon(icon_path))
        self.setFixedSize(self.size())

        self._init_webcam()
        self._init_video_player()
        self._prepare_tcp_client()
    ############## Live Video Stream ##############
    def _prepare_tcp_client(self):
        """Prepare the TCP client but do not connect yet."""
        self.tcp_client = TCPClient(5000)
        self.tcp_thread = QThread()
        self.tcp_client.moveToThread(self.tcp_thread)
        self.tcp_client.frame_ready.connect(self.update_live_preview)
        self.tcp_thread.started.connect(self.tcp_client.receive_video_stream)

        self.play_live_btn.hide()
        self.pause_live_btn.hide()
        self.rewind_btn.hide()
        self.seek_btn.hide()
        self.seek_input.hide()

        self.connect_btn.clicked.connect(self.connect_to_server)
        self.play_live_btn.clicked.connect(self.play_live_stream)
        self.pause_live_btn.clicked.connect(self.pause_live_stream)
        self.rewind_btn.clicked.connect(lambda: self.send_tcp_command("rewind"))
        self.seek_btn.clicked.connect(self.on_seek_button_clicked)

    def stop_live_stream(self):
        """Initiate stopping of the live video stream."""
        if self.tcp_client and self.tcp_thread.isRunning():
            self.tcp_client.send_command("stop")  # Command the client to stop
            # Do not immediately close the connection or stop the thread here

    def connect_to_server(self):
        """Initiate connection to the TCP server and start the thread."""
        ip = self.host_input.text()
        if self.tcp_client.connect_to_server(ip):
            self.tcp_thread.start()
            self.connect_btn.hide()
            self.play_live_btn.show()
            self.rewind_btn.show()
            self.seek_input.show()
            self.host_input.hide()
            print("Connected to TCP server.")
        else:
            print("Failed to connect to TCP server.")

    def on_seek_button_clicked(self):
        position = self.seek_input.text()  # Assuming there's an input field for position
        self.seek_live_stream(position)

    def seek_live_stream(self, position):
        position = convert_time_to_milliseconds(position)
        command = f"seek {position}"
        self.send_tcp_command(command)

    def play_live_stream(self):
        self.send_tcp_command("play")
        self.play_live_btn.hide()
        self.pause_live_btn.show()
        self.seek_btn.show()

    def pause_live_stream(self):
        self.send_tcp_command("pause")
        self.pause_live_btn.hide()
        self.play_live_btn.show()

    def send_tcp_command(self, command):
        """Method to send commands to the TCP server."""
        if self.tcp_client:
            self.tcp_client.send_command(command)
            print(f"Command sent: {command}")


    @pyqtSlot(np.ndarray)
    def update_live_preview(self, frame):
        """Update the live preview with the received video frame."""
        pixmap = process_frame(frame)
        self.live_preview.setPixmap(pixmap.scaled(self.live_preview.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    ############## Video Playback ##############
    def _init_video_player(self):
        # Init buttons
        self.play_btn.hide()
        # Init video playback
        self.video_playback = VideoPlayback(self.video_playback_display)
        self.video_playback.videoLoaded.connect(self.onVideoLoaded)  # Connect signal to slot
        #self.video_playback_display.setAspectRatioMode(Qt.KeepAspectRatio)
        # Connect buttons
        self.browse_btn.clicked.connect(self.video_playback.load_video)
        self.play_btn.clicked.connect(self.toggle_video_playback)

    def onVideoLoaded(self):
        """Slot to show the play button when a video is loaded."""
        self.play_btn.show()
        self.play_btn.setText("Pause")

    def toggle_video_playback(self):
        """Toggle video playback and update button text."""
        self.video_playback.toggle_play_pause()

        # Update button text based on the state after toggling
        if self.video_playback.media_player.state() == QMediaPlayer.PlayingState:
            self.play_btn.setText("Pause")
        else:
            self.play_btn.setText("Play")

    ############## Webcam Capture ##############

    def _init_webcam(self):
        # Init widgets and buttons
        self.stop_webcapture_btn.hide()
        self.webcam_preview.setScaledContents(True)

        # Init webcam capture
        self.webcam_capture = WebcamCapture()

        # Thread and Signal for updating UI
        self.webcam_thread = QThread()
        self.webcam_thread.run = self._capture_frames
        self.webcam_frame_ready.connect(self._update_webcam_preview)

        # Connect buttons
        self.start_webcapture_btn.clicked.connect(self.start_webcam)
        self.stop_webcapture_btn.clicked.connect(self.stop_webcam)

    def start_webcam(self):
        """Start video capture and processing."""
        self.filename, _ = QFileDialog.getSaveFileName(
            self, 'Save video file', filter='Video files (*.mp4)')
        if self.filename:  # Ensure a filename was selected
            if not self.webcam_thread.isRunning():
                self.webcam_thread.start()
            self.start_webcapture_btn.hide()
            self.stop_webcapture_btn.show()

    def stop_webcam(self):
        """Stop the video capture and processing thread."""
        if self.webcam_thread.isRunning():
            self.webcam_thread.requestInterruption()
            self.webcam_thread.quit()
            self.webcam_thread.wait()
        self._clear_webcam_preview()

    def _capture_frames(self):
        """Method to capture frames and process them in a separate thread."""
        self.webcam_capture.start_capture(save_file_path=self.filename)
        while not self.webcam_thread.isInterruptionRequested():
            frame = self.webcam_capture.get_frame()
            if frame is not None:
                # Assuming process_frame returns a QPixmap
                processed_frame = process_frame(frame)
                self.webcam_frame_ready.emit(processed_frame)
        self.webcam_capture.stop_capture()

    @pyqtSlot(QPixmap)
    def _update_webcam_preview(self, pixmap):
        """Slot to update the GUI with a new frame."""
        self.webcam_preview.setPixmap(pixmap)

    def _clear_webcam_preview(self):
        """Clears the webcam preview label after ensuring the thread has stopped."""
        self.webcam_preview.setPixmap(QPixmap())
        self.start_webcapture_btn.show()
        self.stop_webcapture_btn.hide()
