from PySide6.QtWidgets import QGridLayout, QPushButton
from PySide6.QtCore import Qt


class ScheduleButton(QPushButton):
    def __init__(self, text):
        super().__init__()
        self.setFixedWidth(200)
        self.setFixedHeight(38)
        self.setStyleSheet('border:1px solid silver; padding:12px;')
        self.setText(text)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

class ScheduleButtonLayout(QGridLayout):
    def __init__(self):
        super().__init__()
        self.setSpacing(10)
        self.setContentsMargins(5, 10, 10, 10)
        self.btn_sound_create = ScheduleButton(text='Добавить объявление')
        self.btn_sound_delete = ScheduleButton(text='Удалить')
        self.btn_sound_play = ScheduleButton(text='Воспроизвести')
        self.btn_sound_stop = ScheduleButton(text='Остановить')
        self.btn_sound_stop.setHidden(True)

        self.setAlignment(Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)
        self.addWidget(self.btn_sound_create, 0, 0)
        self.addWidget(self.btn_sound_delete, 1, 0)
        self.addWidget(self.btn_sound_play, 0, 1)
        self.addWidget(self.btn_sound_stop, 0, 1)
