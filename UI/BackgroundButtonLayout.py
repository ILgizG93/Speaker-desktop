from PySide6.QtWidgets import QGridLayout
from PySide6.QtCore import Qt

from .SpeakerButton import SpeakerButton

class BackgroundButtonLayout(QGridLayout):
    def __init__(self):
        super().__init__()
        self.setSpacing(10)
        self.setContentsMargins(5, 10, 10, 10)
        self.btn_sound_create = SpeakerButton(text='Добавить объявление')
        self.btn_sound_delete = SpeakerButton(text='Удалить')
        self.btn_sound_play = SpeakerButton(text='Воспроизвести')
        self.btn_sound_stop = SpeakerButton(text='Остановить')

        self.setAlignment(Qt.AlignmentFlag.AlignHCenter|Qt.AlignmentFlag.AlignTop)
        self.addWidget(self.btn_sound_create, 0, 0)
        self.addWidget(self.btn_sound_delete, 1, 0)
        self.addWidget(self.btn_sound_play, 0, 1)
        self.addWidget(self.btn_sound_stop, 1, 1)
