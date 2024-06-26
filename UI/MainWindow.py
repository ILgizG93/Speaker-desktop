import json
import asyncio

import sounddevice as sd
import soundfile as sf
from math import ceil

from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt, QTimer, QUrl, QUrlQuery, QSaveFile, QIODevice
from PySide6.QtGui import QIcon
from PySide6 import QtNetwork

from .Font import RobotoFont
from .ScheduleTable import ScheduleTable
from .ScheduleButtonLayout import ScheduleButtonLayout
from .ScheduleZoneLayout import ScheduleZoneLayout
from .BackgroundTable import BackgroundTable
from .BackgroundButtonLayout import BackgroundButtonLayout
from .AudioTextDialog import AudioTextDialog

current_sort = [4, Qt.SortOrder.AscendingOrder]

class SpeakerException(Exception):
    def __init__(self, message, extra_info):
        super().__init__(message)
        self.extra_info = extra_info


class SpeakerApplication(QMainWindow):
    def __init__(self, settings, interface):
        super().__init__()

        self.current_flight = {}
        self.play_finish_timer = QTimer()
        self.device_id = interface.system_device.get(settings.device.get('name'))
        self.samplerate = settings.device.get('samplerate')

        self.settings = settings
        self.schedule_header = ('', 'Номер рейса', 'Терминал', 'Направление', 'Время прилёта/вылета', 'Маршрут', 'Выход', 'Текст объявления', 'РУС', 'ТАТ', 'АНГ')
        self.schedule_data = [(None,) * len(self.schedule_header)]

        self.setWindowTitle("Speaker 2.0")
        self.setWindowIcon(QIcon("../resources/icons/app/icon.png"))
        self.setGeometry(100, 100, 1280, 720)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.layout = QHBoxLayout(self.central_widget)
        
        # self.btn_settings = QPushButton()
        # self.btn_settings.setIcon(QIcon("../resources/icons/buttons/settings.png"))
        # self.btn_settings.setIconSize(QSize(30, 30))
        # self.btn_settings.setStyleSheet('border:1px solid silver; padding:3px 12px;')
        # self.btn_settings.setText('Настройки')
        # self.btn_settings.setCursor(Qt.CursorShape.PointingHandCursor)
        # self.btn_settings.clicked.connect(self.open_window_settings)

        self.schedule_layout = QVBoxLayout()
        
        self.schedule_label = QLabel()
        self.schedule_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.schedule_label.setText('Объявления')

        self.schedule_table = ScheduleTable(settings=self.settings, header=self.schedule_header)
        self.schedule_table.selectionModel().selectionChanged.connect(self.get_current_sound)

        self.audio_text_dialog = AudioTextDialog(self, settings=self.settings)
        self.player_button_layout = ScheduleButtonLayout()
        self.player_button_layout.btn_sound_create.clicked.connect(self.open_audio_text_dialog)
        self.player_button_layout.btn_sound_play.clicked.connect(lambda: asyncio.run(self.get_sound_file()))
        self.player_button_layout.btn_sound_stop.clicked.connect(self.stop_play)
        # TODO
        # self.player_button_layout.btn_sound_delete.clicked.connect(self.delete_sound)

        self.zone_layout = ScheduleZoneLayout(self.settings)

        self.mainpulation_layout = QHBoxLayout()
        self.mainpulation_layout.addLayout(self.player_button_layout)
        self.mainpulation_layout.addLayout(self.zone_layout)
        
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

        font = RobotoFont()
        self.schedule_label.setFont(font.get_font(18))
        self.schedule_table.setFont(font.get_font())
        self.background_label.setFont(font.get_font(18))
        self.background_table.setFont(font.get_font())
        
        self.timer = QTimer()
        self.timer.setInterval(self.settings.schedule_update_time)
        self.timer.timeout.connect(lambda: asyncio.run(self.get_schedule_data_from_API()))
    
    async def get_schedule_data_from_API(self) -> None:
        self.timer.stop()
        url_file = QUrl(self.settings.api_url+'get_scheduler')
        request = QtNetwork.QNetworkRequest(url_file)
        self.API_manager = QtNetwork.QNetworkAccessManager()
        self.API_manager.get(request)
        self.API_manager.finished.connect(self.refresh_schedule_table)

    def refresh_schedule_table(self, data: QtNetwork.QNetworkReply):
        if data.error() == QtNetwork.QNetworkReply.NetworkError.NoError:
            lang_status = ('✖', '✔')
            self.schedule_data = []
            bytes_string = data.readAll()
            self.schedule_data_origin = json.loads(str(bytes_string, 'utf-8'))
            for data in self.schedule_data_origin:
                self.schedule_data.append((data.get('schedule_id'), data.get('flight_number_full'), data.get('terminal'), data.get('direction'), data.get('plan_datetime'),
                                data.get('path'), data.get('boarding_gates'), data.get('audio_text'),
                                lang_status[data.get('languages').get('RUS').get('display') is True],
                                lang_status[data.get('languages').get('TAT').get('display') is True],
                                lang_status[data.get('languages').get('ENG').get('display') is True]))
            if (len(self.schedule_data) == 0):
                self.schedule_data = [(None,) * len(self.schedule_header)]
            self.schedule_table.table_model.setItems(self.schedule_data)
            # self.schedule_table.sortByColumn(*current_sort)
            print('Schedule data refreshed!')
            self.set_active_row()
            self.timer.start()

    def set_active_row(self) -> None:
        if self.current_flight.get('schedule_id'):
            for row in range(self.schedule_table.model().rowCount()):
                index = self.schedule_table.model().index(row, 0)
                if index.data() == self.current_flight.get('schedule_id'):
                    self.schedule_table.setCurrentIndex(index)
                    return
            self.schedule_table.selectRow(0)
        else:
            self.current_flight = self.schedule_data_origin[0]
            self.schedule_table.selectRow(0)

    def get_current_sound(self):
        row_id = self.schedule_table.model().index(self.schedule_table.currentIndex().row(), 0).data()
        self.current_flight = list(filter(lambda d: d.get('schedule_id') == row_id, self.schedule_data_origin))[0]
        self.current_sound_file = self.settings.file_url+self.current_flight.get('schedule_id')+self.settings.file_format
        self.zone_layout.current_schedule_id = self.current_flight.get('schedule_id')
        self.zone_layout.set_zones(self.current_flight.get('zones'))

    def sound_data_check(self):
        if not self.current_flight.get('terminal'):
            return 'Терминал'
        if int(self.current_flight.get('direction_id')) == 1 and not self.current_flight.get('boarding_gates'):
            return 'Номер выхода'
        return False

    async def get_sound_file(self):
        check = self.sound_data_check()
        if check:
            raise SpeakerException("Ошибка воспроизведения", f"Отсутствуют данные, необходимые для воспроизведения. {check}")

        self.timer.stop()
        self.player_button_layout.btn_sound_play.setDisabled(True)

        url_file = QUrl(self.settings.api_url+'get_scheduler_sound')
        query = QUrlQuery()
        query.addQueryItem('schedule_id', self.current_flight.get('schedule_id'))
        url_file.setQuery(query.query())
        
        request = QtNetwork.QNetworkRequest(url_file)
        self.API_manager = QtNetwork.QNetworkAccessManager()
        reply = self.API_manager.get(request)
        self.API_manager.finished.connect(lambda: asyncio.run(self.save_sound_file(reply)))

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
        sd.play(data, mapping=self.zone_layout.get_active_zones())
        
        self.play_finish_timer.setInterval(duration)
        self.play_finish_timer.timeout.connect(self.stop_play)
        self.play_finish_timer.start()

    def stop_play(self) -> None:
        sd.stop()
        self.timer.start()
        self.play_finish_timer.stop()
        self.player_button_layout.btn_sound_play.setEnabled(True)

    async def get_background_data_from_API(self) -> None:
        url_file = QUrl(self.settings.api_url+'get_audio_background_text')
        request = QtNetwork.QNetworkRequest(url_file)
        self.API_bg_manager = QtNetwork.QNetworkAccessManager()
        self.API_bg_manager.get(request)
        self.API_bg_manager.finished.connect(self.refresh_background_table)

    def refresh_background_table(self, data: QtNetwork.QNetworkReply):
        if data.error() == QtNetwork.QNetworkReply.NetworkError.NoError:
            self.background_data = []
            bytes_string = data.readAll()
            self.background_data_origin = json.loads(str(bytes_string, 'utf-8'))
            for data in self.background_data_origin:
                self.background_data.append((data.get('desciption'), data.get('name')))
            if (len(self.background_data) == 0):
                self.background_data = [(None,) * 2]
            self.background_table.table_model.setItems(self.background_data)
            # self.schedule_table.sortByColumn(*current_sort)
            print('Background data refreshed!')

    def open_audio_text_dialog(self):
        asyncio.run(self.audio_text_dialog.get_flights_from_API())
        asyncio.run(self.audio_text_dialog.get_audio_text_from_API())
        self.audio_text_dialog.exec()
