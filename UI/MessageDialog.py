from PySide6.QtWidgets import QGridLayout, QDialog, QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from .SpeakerButton import SpeakerButton
from .Font import RobotoFont

class MessageDialog(QDialog):
    def __init__(self, parent, message) -> None:
        super().__init__(parent)

        self.setWindowTitle("Системное сообщение")
        self.setWindowIcon(QIcon("icons/app/icon.png"))
        self.setMinimumSize(350, 100)
        self.setMaximumSize(600, 300)
        font = RobotoFont()

        self.layout: QGridLayout = QGridLayout(self)

        self.message_label = QLabel(message)
        self.message_label.setFont(font.get_font())
        self.message_label.setWordWrap(True)

        self.btn_message_close = SpeakerButton(text='Закрыть')
        self.btn_message_close.clicked.connect(self.close)

        self.layout.addWidget(self.message_label, 0, 0, alignment=Qt.AlignmentFlag.AlignTop)
        self.layout.addWidget(self.btn_message_close, 1, 0, alignment=Qt.AlignmentFlag.AlignCenter)
