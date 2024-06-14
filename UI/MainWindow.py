import json
import asyncio
from typing import Optional

import sounddevice as sd
import soundfile as sf
import av
from math import ceil

from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QTableView, QHBoxLayout, QHeaderView, QPushButton, QFrame, QItemDelegate, QAbstractItemView
from PySide6.QtCore import QObject, Qt, QTimer, QSize, QThreadPool, QRunnable, Slot
from PySide6.QtGui import QIcon, QFont
from PySide6 import QtNetwork

from .TableModel import TableModel

API_URL = 'http://localhost:8000/speaker/'

current_sort = [4, Qt.AscendingOrder]

def get_sound_duration(sound_file):
    return ceil(av.open(sound_file).streams.audio[0].container.duration / 1_000_000)

class SpeakerException(Exception):
    def __init__(self, message, extra_info):
        super().__init__(message)
        self.extra_info = extra_info


class AlignDelegate(QItemDelegate):
    def __init__(self, columns, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.columns = columns

    def paint(self, painter, option, index) -> None:
        if index.column() in self.columns:
            option.displayAlignment = Qt.AlignCenter
        else:
            option.displayAlignment = Qt.AlignLeft | Qt.AlignVCenter
        QItemDelegate.paint(self, painter, option, index)


class SpeakerApplication(QMainWindow):
    def __init__(self, settings, interface):
        super().__init__()
        
        self.playlist = []
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
        
        self.layout = QVBoxLayout(self.central_widget)
        
        self.top_layout = QHBoxLayout()
        self.top_layout.setAlignment(Qt.AlignRight)
        
        self.btn_settings = QPushButton()
        self.btn_settings.setIcon(QIcon("../resources/icons/buttons/settings.png"))
        self.btn_settings.setIconSize(QSize(30, 30))
        self.btn_settings.setStyleSheet('border:1px solid silver; padding:3px 12px;')
        self.btn_settings.setText('Настройки')
        self.btn_settings.setCursor(Qt.PointingHandCursor)
        self.btn_settings.clicked.connect(self.open_window_settings)
        
        self.top_layout.addWidget(self.btn_settings)
        self.layout.addLayout(self.top_layout)

        self.table_layout = QHBoxLayout()

        # self.btn_sound_refresh = QPushButton()
        # self.btn_sound_refresh.setFixedHeight(38)
        # self.btn_sound_refresh.setStyleSheet('border:1px solid silver; padding:12px;')
        # self.btn_sound_refresh.setText('Обновить расписание')
        # self.btn_sound_refresh.setCursor(Qt.PointingHandCursor)
        # self.btn_sound_refresh.clicked.connect(lambda: asyncio.run(self.get_schedule_data_from_API()))

        self.btn_sound_create = QPushButton()
        self.btn_sound_create.setFixedHeight(38)
        self.btn_sound_create.setStyleSheet('border:1px solid silver; padding:12px;')
        self.btn_sound_create.setText('Добавить новое объявление')
        self.btn_sound_create.setCursor(Qt.PointingHandCursor)
        self.btn_sound_create.clicked.connect(self.open_window_sound_add)
        
        self.btn_sound_play = QPushButton()
        self.btn_sound_play.setFixedWidth(200)
        self.btn_sound_play.setFixedHeight(38)
        self.btn_sound_play.setStyleSheet('border:1px solid silver; padding:12px;')
        self.btn_sound_play.setText('Воспроизвести')
        self.btn_sound_play.setCursor(Qt.PointingHandCursor)
        self.btn_sound_play.clicked.connect(self.play_sound)
        
        self.btn_sound_stop = QPushButton()
        self.btn_sound_stop.setFixedWidth(200)
        self.btn_sound_stop.setFixedHeight(38)
        self.btn_sound_stop.setStyleSheet('border:1px solid silver; padding:12px;')
        self.btn_sound_stop.setText('Остановить')
        self.btn_sound_stop.setCursor(Qt.PointingHandCursor)
        self.btn_sound_stop.clicked.connect(self.stop_play)

        self.btn_sound_delete = QPushButton()
        self.btn_sound_delete.setFixedWidth(200)
        self.btn_sound_delete.setFixedHeight(38)
        self.btn_sound_delete.setStyleSheet('border:1px solid silver; padding:12px;')
        self.btn_sound_delete.setText('Удалить')
        self.btn_sound_delete.setCursor(Qt.PointingHandCursor)
        self.btn_sound_delete.clicked.connect(self.delete_sound)

        self.current_row_id = None
        self.main_table_model = TableModel(self, self.schedule_header)
        self.main_table = QTableView()
        self.main_table.setModel(self.main_table_model)
        self.main_table.setColumnHidden(0, True)
        self.main_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.main_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.main_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.main_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.main_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        self.main_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.main_table.horizontalHeader().setSectionResizeMode(7, QHeaderView.Stretch)
        self.main_table.horizontalHeader().setSectionResizeMode(8, QHeaderView.Fixed)
        self.main_table.horizontalHeader().setSectionResizeMode(9, QHeaderView.Fixed)
        self.main_table.horizontalHeader().setSectionResizeMode(10, QHeaderView.Fixed)
        self.main_table.setItemDelegate(AlignDelegate((2, 3, 4, 6, 8, 9, 10)))
        self.main_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.main_table.setSelectionMode(QAbstractItemView.SingleSelection)
        font = QFont("'Poppins', sans-serif", 11)
        self.main_table.setFont(font)
        # self.main_table.setSortingEnabled(True)

        self.table_layout_buttons = QVBoxLayout()
        self.table_layout_buttons.setAlignment(Qt.AlignLeft)
        self.table_layout_buttons.addWidget(self.btn_sound_create)
        self.table_layout_buttons.addWidget(self.btn_sound_play)
        self.table_layout_buttons.addWidget(self.btn_sound_stop)
        self.table_layout_buttons.addWidget(self.btn_sound_delete)
        self.table_layout_buttons.addStretch()

        self.table_layout.addWidget(self.main_table)
        self.table_layout.addLayout(self.table_layout_buttons)

        self.bottom_layout = QHBoxLayout()
        self.bottom_layout.setAlignment(Qt.AlignRight)

        self.separator = QFrame()
        self.separator.setFrameShape(QFrame.VLine)
        self.separator.setLineWidth(5)
        self.bottom_layout.addWidget(self.separator)

        from UI.DeviceVolumeLayout import DeviceVolumeLayout
        output_devices = self.settings.device.get('outputs')
        for i in range(1, len(output_devices)+1):
            current_device = output_devices.get(str(i))
            self.bottom_layout.addLayout(DeviceVolumeLayout(interface, current_device))

        self.layout.addLayout(self.table_layout)
        self.separator = QFrame()
        self.separator.setFrameShape(QFrame.HLine)
        self.separator.setLineWidth(3)
        # self.layout.addWidget(self.separator)
        # self.layout.addLayout(self.bottom_layout)

        self.threadpool = QThreadPool()
        self.timer = QTimer()
        self.timer.setInterval(self.settings.schedule_update_time)
        self.timer.timeout.connect(lambda: asyncio.run(self.get_schedule_data_from_API()))
    
    async def get_fake_schedule_data(self) -> None:
        with open('../response_1718366946287.json', 'rb') as json_file:
            data = json_file.read()
        self.refresh_schedule_table(data)
    
    async def get_schedule_data_from_API(self) -> None:
        self.timer.stop()
        request = QtNetwork.QNetworkRequest(API_URL+'get_scheduler')
        self.network_manager = QtNetwork.QNetworkAccessManager()
        self.network_reply = self.network_manager.get(request)
        self.network_manager.finished.connect(self.refresh_schedule_table)

    def refresh_schedule_table(self, data):
        if self.network_reply.error() == QtNetwork.QNetworkReply.NetworkError.NoError:
            lang_status = ('✖', '✔')
            self.schedule_data = []
            bytes_string = self.network_reply.readAll()
            self.schedule_data_origin = json.loads(str(bytes_string, 'utf-8'))
            for data in self.schedule_data_origin:
                self.schedule_data.append((data.get('schedule_id'), data.get('flight_number_full'), data.get('terminal'), data.get('direction'), data.get('plan_datetime'),
                                data.get('path'), data.get('boarding_gates'), data.get('audio_text'), 
                                lang_status[data.get('languages').get('RUS').get('display') is True],
                                lang_status[data.get('languages').get('TAT').get('display') is True],
                                lang_status[data.get('languages').get('ENG').get('display') is True]))
            if (len(self.schedule_data) == 0):
                self.schedule_data = [(None,) * len(self.schedule_header)]
            self.main_table_model = TableModel(self, self.schedule_header, self.schedule_data)
            self.main_table.setModel(self.main_table_model)
            # self.main_table.sortByColumn(*current_sort)
            self.set_active_row()
        print('Schedule data refreshed!')
        self.timer.start()

    def get_current_row_id(self):
        return self.main_table.model().index(self.main_table.currentIndex().row(), 0).data()

    def set_active_row(self) -> None:
        if self.current_row_id:
            for row in range(self.main_table.model().rowCount()):
                index = self.main_table.model().index(row, 0)
                if index.data() == self.current_row_id:
                    self.main_table.setCurrentIndex(index)
                    return
    
    def playlist_prepare(self, schedule_id):
        schedule = list(filter(lambda data: data.get('schedule_id') == schedule_id, self.schedule_data_origin))[0]
        languages_sorted = dict(sorted(schedule.get('languages').items(), key=lambda item: item[1].get('order', 0)))
        for key, language in languages_sorted.items():
            if language.get('display'):
                id = '_'.join((schedule_id, key))
                self.playlist.append(id)

    def play_sound(self, is_next: bool=False) -> None:
        self.timer.stop()
        self.btn_sound_play.setDisabled(True)
        schedule_id = self.get_current_row_id()
        if schedule_id:
            if not self.playlist and not is_next:
                self.playlist_prepare(schedule_id)
            file_name = 'C:/PythonProjects/airport/modules/speaker/audio_files/'+self.playlist[0]+'.wav'
            data, fs = sf.read(file_name)
            sd.stop()
            sd.default.device = self.device_id
            sd.default.samplerate = self.samplerate
            sd.play(data, mapping=[2, 5, 6, 8])
            duration = (ceil(av.open(file_name).streams.audio[0].container.duration / 1_000_000)+0.5) * 1_000
            self.play_next_timer = QTimer()
            self.play_next_timer.setInterval(duration)
            self.play_next_timer.timeout.connect(self.play_next)
            self.play_next_timer.start()
        else:
            self.btn_sound_play.setEnabled(True)
            raise SpeakerException("Ошибка воспроизведения", "Чтобы проиграть объявление, его нужно выбрать.")


    def play_next(self) -> None:
        self.playlist.pop(0)
        if self.playlist:
            self.play_sound()
        else:
            self.stop_play()


    def stop_play(self) -> None:
        sd.stop()
        self.playlist = []
        self.timer.start()
        self.play_next_timer.stop()
        self.btn_sound_play.setEnabled(True)


    def delete_sound(self) -> None:
        pass

    def open_window_settings(self):
        pass

    def open_window_templates(self):
        pass

    def open_window_sound_add(self):
        pass
