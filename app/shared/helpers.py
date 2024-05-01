from PyQt5.QtGui import QPixmap, QImage
import cv2

def process_frame(frame):
    """Convert the frame to a QPixmap object."""
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    image = QImage(frame.data, frame.shape[1], frame.shape[0], QImage.Format_RGB888)
    pixmap = QPixmap.fromImage(image)
    return pixmap
    
def convert_time_to_milliseconds(time_str):
    """Convert time from 'HH:MM:SS' format to milliseconds."""
    if ':' in time_str:
        hours, minutes, seconds = map(int, time_str.split(':'))
        total_seconds = (hours * 3600) + (minutes * 60) + seconds
        milliseconds = total_seconds * 1000
        return milliseconds
    else:
        return 0  # Default to 0 if format is incorrect
