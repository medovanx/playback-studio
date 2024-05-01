import sys
from PyQt5.QtWidgets import QApplication
from gui.pbs_window import PlaybackStudio

if __name__ == "__main__":
    app = QApplication([])
    window = PlaybackStudio()
    window.show()
    sys.exit(app.exec_())