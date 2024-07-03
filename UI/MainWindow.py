import json
import asyncio
import requests

import sounddevice as sd
import soundfile as sf
from math import ceil

from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt, QTimer, QUrl, QUrlQuery, QSaveFile, QIODevice, QJsonDocument
from PySide6.QtGui import QIcon, QAction
from PySide6 import QtNetwork

from settings import SpeakerSetting
from WinAPI.Device import AudioInterface
from .Font import RobotoFont
from .ScheduleTable import ScheduleTable
from .ScheduleButtonLayout import ScheduleButtonLayout
from .ScheduleZoneLayout import ScheduleZoneLayout
from .BackgroundTable import BackgroundTable
from .BackgroundButtonLayout import BackgroundButtonLayout
from .AudioTextDialog import AudioTextDialog



class SpeakerException(Exception):
    def __init__(self, message, extra_info):
        super().__init__(message)
        self.extra_info = extra_info


class SpeakerApplication(QMainWindow):
    def __init__(self, settings: SpeakerSetting, interface: AudioInterface):
        super().__init__()
        font = RobotoFont()

        zones_request = requests.get(settings.api_url+'get_zones')
        self.zones = zones_request.json()


        self.play_finish_timer = QTimer()
        self.device_id = interface.system_device.get(settings.device.get('name'))
        self.samplerate = settings.device.get('samplerate')

        self.settings = settings
        self.schedule_header = ('', 'Номер рейса', '', 'Время (План)', 'Время (Расч.)', 'Текст объявления', 'Маршрут', 'РУС', 'ТАТ', 'АНГ', 'Терминал', 'Выход', *[str(zone.get('id')) for zone in self.zones])
        self.schedule_data = [(None,) * len(self.schedule_header)]

        self.setWindowTitle("Speaker 2.0")
        self.setWindowIcon(QIcon("../resources/icons/app/icon.png"))
        self.setGeometry(100, 100, 1280, 720)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.layout: QHBoxLayout = QHBoxLayout(self.central_widget)

        menu = self.menuBar()
        menu.setFont(font.get_font(10))

        setting_action = QAction("&Настройки", self)
        setting_action.triggered.connect(lambda: print('Настройки'))
        setting_action.setFont(font.get_font(10))
        menu.addAction(setting_action)
        setting_action = QAction("&Зоны", self)
        setting_action.triggered.connect(lambda: print('Зоны'))
        setting_action.setFont(font.get_font(10))
        menu.addAction(setting_action)
        setting_action = QAction("&Объявления", self)
        setting_action.triggered.connect(lambda: print('Объявления'))
        setting_action.setFont(font.get_font(10))
        menu.addAction(setting_action)
        setting_action = QAction("&Фоновые объявления", self)
        setting_action.triggered.connect(lambda: print('Фоновые объявления'))
        setting_action.setFont(font.get_font(10))
        menu.addAction(setting_action)

        self.audio_text_dialog = AudioTextDialog(self, settings=self.settings)

        self.schedule_layout = QVBoxLayout()
        
        self.schedule_label = QLabel()
        self.schedule_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.schedule_label.setText('Объявления')

        self.schedule_table = ScheduleTable(self.schedule_header, self.zones, self.settings)
        self.schedule_table.selectionModel().selectionChanged.connect(self.get_current_sound)

        self.schedule_button_layout = ScheduleButtonLayout()
        self.schedule_button_layout.btn_sound_create.clicked.connect(self.open_audio_text_dialog)
        self.schedule_button_layout.btn_sound_play.clicked.connect(lambda: asyncio.run(self.get_sound_file()))
        self.schedule_button_layout.btn_sound_stop.clicked.connect(self.stop_play)
        self.schedule_button_layout.btn_sound_delete.clicked.connect(self.schedule_table.delete_schedule)

        self.zone_layout = ScheduleZoneLayout(self.settings, self.zones)

        self.mainpulation_layout = QHBoxLayout()
        self.mainpulation_layout.addLayout(self.schedule_button_layout)
        # self.mainpulation_layout.addLayout(self.zone_layout)
        
        self.schedule_layout.addWidget(self.schedule_label)
        self.schedule_layout.addWidget(self.schedule_table)
        self.schedule_layout.addLayout(self.mainpulation_layout)
        
        self.background_layout = QVBoxLayout()
        
        self.background_label = QLabel()
        self.background_label.setMaximumWidth(340)
        self.background_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.background_label.setText('Фоновые объявления')
        
        self.background_table = BackgroundTable()

        self.bg_button_layout = BackgroundButtonLayout()
        # TODO
        # self.bg_button_layout.btn_sound_create.clicked.connect()
        # self.bg_button_layout.btn_sound_play.clicked.connect(lambda: asyncio.run(self.get_sound_file()))
        # self.bg_button_layout.btn_sound_stop.clicked.connect(self.stop_play)
        # self.bg_button_layout.btn_sound_delete.clicked.connect(self.delete_sound)

        self.background_layout.addWidget(self.background_label)
        self.background_layout.addWidget(self.background_table)
        self.background_layout.addLayout(self.bg_button_layout)

        self.layout.addLayout(self.schedule_layout)
        self.layout.addLayout(self.background_layout)

        self.schedule_label.setFont(font.get_font(18))
        self.background_label.setFont(font.get_font(18))
        self.background_table.setFont(font.get_font())

    def get_current_sound(self):
        row_id = self.schedule_table.item(self.schedule_table.currentRow(), 0).text()
        self.schedule_table.current_flight = list(filter(lambda d: d.get('schedule_id') == row_id, self.schedule_table.schedule_data_origin))[0]
        self.current_sound_file = self.settings.file_url+self.schedule_table.current_flight.get('schedule_id')+self.settings.file_format
        self.schedule_table.current_schedule_id = self.schedule_table.current_flight.get('schedule_id')
        print(row_id)

    def sound_data_check(self):
        if not self.schedule_table.current_flight.get('terminal'):
            return 'Терминал'
        if int(self.schedule_table.current_flight.get('direction_id')) == 1 and not self.schedule_table.current_flight.get('boarding_gates'):
            return 'Номер выхода'
        return False

    async def get_sound_file(self):
        check = self.sound_data_check()
        if check:
            raise SpeakerException("Ошибка воспроизведения", f"Отсутствуют данные, необходимые для воспроизведения. {check}")

        self.schedule_table.timer.stop()
        self.schedule_button_layout.btn_sound_play.setHidden(True)
        self.schedule_button_layout.btn_sound_stop.setVisible(True)

        url_file = QUrl(self.settings.api_url+'get_scheduler_sound')
        query = QUrlQuery()
        query.addQueryItem('schedule_id', self.schedule_table.current_flight.get('schedule_id'))
        url_file.setQuery(query.query())
        
        request = QtNetwork.QNetworkRequest(url_file)
        self.API_manager = QtNetwork.QNetworkAccessManager()
        request.setHeader(QtNetwork.QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")
        body = QJsonDocument({'languages': self.schedule_table.get_current_languages()})
        
        reply = self.API_manager.post(request, body.toJson())
        self.API_manager.finished.connect(lambda: asyncio.run(self.save_sound_file(reply)))
        
        # reply = self.API_manager.get(request)
        # self.API_manager.finished.connect(lambda: asyncio.run(self.save_sound_file(reply)))

    async def save_sound_file(self, data: QtNetwork.QNetworkReply):
        self.file = QSaveFile(self.current_sound_file)
        data = data.readAll()
        self.file.open(QIODevice.OpenModeFlag.WriteOnly)
        self.file.write(data)
        self.file.commit()
        self.play_sound()

    def play_sound(self) -> None:
        file = sf.SoundFile(self.current_sound_file)
        duration = ceil(file.frames / file.samplerate) * 1_000
        
        data, _ = sf.read(self.current_sound_file)
        sd.default.device = self.device_id
        sd.default.samplerate = self.samplerate
        sd.play(data, mapping=self.schedule_table.get_current_zones())
        
        self.play_finish_timer.setInterval(duration)
        self.play_finish_timer.timeout.connect(self.stop_play)
        self.play_finish_timer.start()

    def stop_play(self) -> None:
        sd.stop()
        self.schedule_table.timer.start()
        self.play_finish_timer.stop()
        self.schedule_button_layout.btn_sound_play.setVisible(True)
        self.schedule_button_layout.btn_sound_stop.setHidden(True)

    async def get_background_data_from_API(self) -> None:
        url_file = QUrl(self.settings.api_url+'get_audio_background_text')
        request = QtNetwork.QNetworkRequest(url_file)
        self.API_bg_manager = QtNetwork.QNetworkAccessManager()
        self.API_bg_manager.get(request)
        self.API_bg_manager.finished.connect(self.refresh_background_table)

    def refresh_background_table(self, data: QtNetwork.QNetworkReply) -> None:
        if data.error() == QtNetwork.QNetworkReply.NetworkError.NoError:
            self.background_data = []
            bytes_string = data.readAll()
            self.background_data_origin = json.loads(str(bytes_string, 'utf-8'))
            for data in self.background_data_origin:
                self.background_data.append((data.get('desciption'), data.get('name')))
            if (len(self.background_data) == 0):
                self.background_data = [(None,) * 2]
            self.background_table.table_model.setItems(self.background_data)
            print('Background data refreshed!')

    def open_audio_text_dialog(self) -> None:
        asyncio.run(self.audio_text_dialog.get_flights_from_API())
        asyncio.run(self.audio_text_dialog.get_audio_text_from_API())
        self.audio_text_dialog.audio_text_info_layout.itemAt(0).widget().setText('')
        self.audio_text_dialog.exec()