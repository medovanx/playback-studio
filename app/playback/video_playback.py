from PyQt5.QtMultimedia import QMediaPlayer
from PyQt5.QtWidgets import QWidget, QFileDialog
from PyQt5.QtMultimedia import QMediaContent
from PyQt5.QtCore import QUrl
from PyQt5.QtCore import pyqtSignal

class VideoPlayback(QWidget):
    videoLoaded = pyqtSignal()  # Signal to emit when a video is loaded

    def __init__(self, video_display):
        super().__init__()
        self.media_player = QMediaPlayer(None, QMediaPlayer.VideoSurface)   # Create a media player object, parent: None, type: Video
        self.media_player.setVideoOutput(video_display)     # Set the video output to the video widget

    def load_video(self):
        """Load a video file using a file dialog."""
        self.filename, _ = QFileDialog.getOpenFileName(self, 'Select video file', filter='Video files (*.mp4)')
        if self.filename:  # Check if a file was selected
            self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(self.filename)))
            self.media_player.play()
            self.videoLoaded.emit()  # Emit the signal to indicate that a video is loaded
            
    def toggle_play_pause(self):
        """Toggle play/pause based on current state."""
        if self.media_player.state() == QMediaPlayer.PlayingState:
            self.media_player.pause()
        elif self.media_player.state() == QMediaPlayer.PausedState:
            self.media_player.play()
        else:
            self.media_player.play()