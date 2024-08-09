from PySide6.QtWidgets import QPushButton
from PySide6.QtCore import Qt

class SpeakerButton(QPushButton):
    def __init__(self, text, width: int = 160, height: int = 38):
        super().__init__()
        self.setFixedWidth(width)
        self.setFixedHeight(height)
        self.setStyleSheet('border:1px solid silver; padding:12px;')
        self.setText(text)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
