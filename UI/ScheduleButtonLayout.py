from PySide6.QtWidgets import QGridLayout
from PySide6.QtCore import Qt

from .SpeakerButton import SpeakerButton

class ScheduleButtonLayout(QGridLayout):
    def __init__(self):
        super().__init__()
        self.setSpacing(10)
        self.setContentsMargins(5, 10, 10, 10)
        self.btn_sound_create = SpeakerButton(text='Добавить объявление', width=200)
        self.btn_sound_delete = SpeakerButton(text='Удалить', width=200)
        self.btn_sound_play = SpeakerButton(text='Воспроизвести', width=200)
        self.btn_sound_stop = SpeakerButton(text='Остановить', width=200)
        self.btn_sound_stop.setHidden(True)

        self.setAlignment(Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)
        self.addWidget(self.btn_sound_create, 0, 0)
        self.addWidget(self.btn_sound_delete, 1, 0)
        self.addWidget(self.btn_sound_play, 0, 1)
        self.addWidget(self.btn_sound_stop, 0, 1)
