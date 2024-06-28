import json
import asyncio

import sounddevice as sd
import soundfile as sf
from math import ceil

from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView
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

        [checkbox.clicked.connect(self.zone_checkbox_click) for checkbox in self.zone_layout.checkboxes]

        self.mainpulation_layout = QHBoxLayout()
        self.mainpulation_layout.addLayout(self.player_button_layout)
        self.mainpulation_layout.addLayout(self.zone_layout)

        import requests
        req = requests.get(self.settings.api_url+'get_zones')
        self.zones = req.json()


        self.table = QTableWidget(0, len(self.schedule_header)+len(self.zones), self)
        self.table.setMinimumWidth(300)
        
        self.table.setHorizontalHeaderLabels(('', 'Номер рейса', '', 'Время рейса', 'Текст объявления', 'Маршрут', *[str(zone.get('id')) for zone in self.zones], 'Терминал', 'Выход', 'РУС', 'ТАТ', 'АНГ'))
        self.table.setColumnHidden(0, True)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        for i in range(0, len(self.zones)):
            self.table.horizontalHeader().setSectionResizeMode(6+i, QHeaderView.ResizeMode.Fixed)
            self.table.setColumnWidth(6+i, 32)
        self.table.horizontalHeader().setSectionResizeMode(len(self.zones)+6, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(len(self.zones)+7, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(len(self.zones)+8, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(len(self.zones)+9, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(len(self.zones)+10, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(len(self.zones)+8, 32)
        self.table.setColumnWidth(len(self.zones)+9, 32)
        self.table.setColumnWidth(len(self.zones)+10, 32)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.selectionModel().selectionChanged.connect(self.get_current_sound)

        
        self.schedule_layout.addWidget(self.schedule_label)
        # self.schedule_layout.addWidget(self.schedule_table)
        self.schedule_layout.addWidget(self.table)
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
        self.table.setFont(font.get_font())
        
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
            self.schedule_data = []
            bytes_string = data.readAll()
            self.schedule_data_origin = json.loads(str(bytes_string, 'utf-8'))
            for data in self.schedule_data_origin:
                self.schedule_data.append((data.get('schedule_id'), data.get('flight_number_full'), data.get('direction'), data.get('flight_time'), data.get('audio_text'),
                                data.get('airport'), 
                                *list(map(lambda i: True if i[0]+1 in data.get('zones') else False, enumerate(self.zones))),
                                # *[True for i in range(0, len(self.zones)) if i in data.get('zones')], 
                                data.get('terminal'), data.get('boarding_gates'),
                                data.get('languages').get('RUS').get('display'),
                                data.get('languages').get('TAT').get('display'),
                                data.get('languages').get('ENG').get('display')))
            if (len(self.schedule_data) == 0):
                self.schedule_data = [(None,) * len(self.schedule_header)]

            if (len(self.schedule_data) == 0):
                self.table.setRowCount(0)
            else:
                self.table.setRowCount(len(self.schedule_data))
                for row_indx, data in enumerate(self.schedule_data):
                    for col_indx, item in enumerate(data):
                        if col_indx in [2,3, 6+len(self.zones), 6+len(self.zones)+1]:
                            element = QTableWidgetItem(item)
                            element.setTextAlignment(Qt.AlignmentFlag.AlignHCenter|Qt.AlignmentFlag.AlignVCenter)
                            self.table.setItem(row_indx, col_indx, element)
                        elif col_indx in [i for i in range(6, 6+len(self.zones))]:
                            widget = QWidget()
                            checkbox = QCheckBox()
                            checkbox.setChecked(item)
                            checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
                            layoutH = QHBoxLayout(widget)
                            layoutH.addWidget(checkbox)
                            layoutH.setAlignment(Qt.AlignmentFlag.AlignCenter)
                            layoutH.setContentsMargins(0, 0, 0, 0)
                            self.table.setCellWidget(row_indx, col_indx, widget)
                        elif col_indx in [i for i in range(8+len(self.zones), 8+len(self.zones)+3)] and item:
                            widget = QWidget()
                            checkbox = QCheckBox()
                            checkbox.setChecked(True)
                            checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
                            layoutH = QHBoxLayout(widget)
                            layoutH.addWidget(checkbox)
                            layoutH.setAlignment(Qt.AlignmentFlag.AlignCenter)
                            layoutH.setContentsMargins(0, 0, 0, 0)
                            self.table.setCellWidget(row_indx, col_indx, widget)
                        else:
                            self.table.setItem(row_indx, col_indx, QTableWidgetItem(item))

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
        # row_id = self.schedule_table.model().index(self.schedule_table.currentIndex().row(), 0).data()
        row_id = self.table.item(self.table.currentRow(), 0).text()
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
            print('Background data refreshed!')

    def open_audio_text_dialog(self):
        asyncio.run(self.audio_text_dialog.get_flights_from_API())
        asyncio.run(self.audio_text_dialog.get_audio_text_from_API())
        self.audio_text_dialog.audio_text_info_layout.itemAt(0).widget().setText('')
        self.audio_text_dialog.exec()

    def zone_checkbox_click(self):
        self.current_flight['zones'] = self.zone_layout.get_active_zones()
        self.zone_layout.update_zones()