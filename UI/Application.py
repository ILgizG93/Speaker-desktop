import requests

from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QAbstractItemView, QCheckBox, QFrame
from PySide6.QtCore import Qt, QTimer, QUrl, QUrlQuery, QSaveFile, QIODevice, QJsonDocument, QSize, Signal
from PySide6.QtGui import QIcon
from PySide6 import QtNetwork

from UI.Font import RobotoFont
from globals import settings, logger, zones, exit_program_bcs_err

class SpeakerException(Exception):
    def __init__(self, message, extra_info) -> None:
        super().__init__(message)
        self.extra_info = extra_info

class SpeakerApplication(QMainWindow):

    def __init__(self) -> None:
        super().__init__()
        
        self.user_uuid = 'e8c1c5d1-dfa5-4252-ad97-5d3d222794e1'
        self._font: RobotoFont = RobotoFont()

        logger.info(f'Начало загрузки формы приложения')

        self.setWindowTitle("Speaker 2.0")
        self.setWindowIcon(QIcon("../resources/icons/app/icon.png"))
        self.setGeometry(100, 100, 1280, 720)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.layout: QHBoxLayout = QHBoxLayout(self.central_widget)

        from UI.CustomTableView import ScheduleTable
        self.schedule_layout = QVBoxLayout()
        self.schedule_table = ScheduleTable()
        self.schedule_layout.addWidget(self.schedule_table)
        # self.setStyleSheet("font-family: Roboto; font-size: 12px")

        from UI.CustomTableView import BackgroundTable
        self.background_layout = QVBoxLayout()
        self.background_table = BackgroundTable()
        self.background_layout.addWidget(self.background_table)

        self.layout.addLayout(self.schedule_layout)
        self.layout.addLayout(self.background_layout)

        self.schedule_table.setStyleSheet("font-size: 15px")
        self.background_table.setStyleSheet("font-size: 15px")

        from .SpeakerStatusBar import speaker_status_bar
        self.speaker_status_bar = speaker_status_bar
        self.setStatusBar(speaker_status_bar)
        self.statusBar().setStyleSheet("font-size: 16px")
