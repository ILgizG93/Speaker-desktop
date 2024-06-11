import json
import asyncio
from typing import Optional


from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QTableView, QHBoxLayout, QHeaderView, QPushButton, QFrame, QItemDelegate, QAbstractItemView
from PySide6.QtCore import QObject, Qt, QTimer, QSize, QThreadPool
from PySide6.QtGui import QIcon, QFont
from PySide6 import QtNetwork

from .TableModel import TableModel
from Player.play_long_file import Player
from Player.AudioTrigger import AudioTrigger

API_URL = 'http://localhost:8000/speaker/'

current_sort = [4, Qt.AscendingOrder]

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
        self.audio_trigger = AudioTrigger()
        self.audio_trigger.finished.connect(self.play_next)

        self.settings = settings
        self.schedule_header = ('', 'Номер рейса', 'Терминал', 'Направление', 'Время прилёта/вылета', 'Маршрут', 'Выход', 'Текст объявления', 'РУС', 'ТАТ', 'АНГ')
        self.schedule_data = [(None,) * len(self.schedule_header)]

        self.current_track_index = -1

        self.current_volume = 50

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

        self.btn_sound_add = QPushButton()
        self.btn_sound_add.setFixedHeight(38)
        self.btn_sound_add.setStyleSheet('border:1px solid silver; padding:12px;')
        self.btn_sound_add.setText('Добавить новое объявление')
        self.btn_sound_add.setCursor(Qt.PointingHandCursor)
        self.btn_sound_add.clicked.connect(self.open_window_sound_add)

        self.btn_sound_refresh = QPushButton()
        self.btn_sound_refresh.setFixedHeight(38)
        self.btn_sound_refresh.setStyleSheet('border:1px solid silver; padding:12px;')
        self.btn_sound_refresh.setText('Обновить расписание')
        self.btn_sound_refresh.setCursor(Qt.PointingHandCursor)
        self.btn_sound_refresh.clicked.connect(lambda: asyncio.run(self.get_fake_schedule_data()))

        self.top_layout.addWidget(self.btn_settings)
        self.top_layout.addWidget(self.btn_sound_add)
        self.top_layout.addWidget(self.btn_sound_refresh)
        self.layout.addLayout(self.top_layout)


        self.table_layout = QHBoxLayout()

        self.current_row_id = None
        # self.main_table_model = TableModel(self, self.schedule_header, self.schedule_data)
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

        self.main_table.clicked.connect(self.get_current_row_id)

        self.table_layout.addWidget(self.main_table)

        self.sliders_layout = QHBoxLayout()
        self.sliders_layout.setAlignment(Qt.AlignRight)

        self.playlist = []
        self.playlist_header = ('', 'Номер рейса', 'Направление', 'Текст объявления', 'Язык', 'Продолжительность', 'Проиграть в')
        # self.playlist_table_model = TableModel(self, self.playlist_header, [(None,) * len(self.playlist_header)])
        self.playlist_table_model = TableModel(self, self.playlist_header)
        self.playlist_table = QTableView()
        self.playlist_table.setFixedHeight(300)
        self.playlist_table.setMinimumWidth(800)
        self.playlist_table.setMaximumWidth(1000)
        self.playlist_table.setModel(self.playlist_table_model)
        self.playlist_table.setColumnHidden(0, True)
        self.playlist_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.playlist_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.playlist_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.playlist_table.setColumnWidth(3, 220)
        self.playlist_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.playlist_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Fixed)
        self.playlist_table.setColumnWidth(5, 140)
        self.playlist_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Stretch)
        self.playlist_table.setItemDelegate(AlignDelegate((5, 6)))
        self.playlist_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.playlist_table.setSelectionMode(QAbstractItemView.SingleSelection)
        font = QFont("'Poppins', sans-serif", 11)
        self.playlist_table.setFont(font)
        self.sliders_layout.addWidget(self.playlist_table)

        self.test_button = QPushButton()
        self.test_button.setFixedHeight(38)
        self.test_button.setStyleSheet('border:1px solid silver; padding:12px;')
        self.test_button.setText('Добавить объявление в очередь')
        self.test_button.setCursor(Qt.PointingHandCursor)
        self.test_button.clicked.connect(self.append_to_playlist)
        self.sliders_layout.addWidget(self.test_button)

        self.test_button = QPushButton()
        self.test_button.setFixedHeight(38)
        self.test_button.setStyleSheet('border:1px solid silver; padding:12px;')
        self.test_button.setText('Воспроизвести')
        self.test_button.setCursor(Qt.PointingHandCursor)
        self.test_button.clicked.connect(self.play_sound)
        self.sliders_layout.addWidget(self.test_button)


        self.separator = QFrame()
        self.separator.setFrameShape(QFrame.VLine)
        self.separator.setLineWidth(5)
        self.sliders_layout.addWidget(self.separator)

        from UI.DeviceVolumeLayout import DeviceVolumeLayout
        output_devices = self.settings.device.get('outputs')
        for i in range(1, len(output_devices)+1):
            current_device = output_devices.get(str(i))
            self.sliders_layout.addLayout(DeviceVolumeLayout(interface, current_device))

        self.layout.addLayout(self.table_layout)
        self.separator = QFrame()
        self.separator.setFrameShape(QFrame.HLine)
        self.separator.setLineWidth(3)
        self.layout.addWidget(self.separator)
        self.layout.addLayout(self.sliders_layout)

        self.threadpool = QThreadPool()
        self.timer = QTimer()
        self.timer.setInterval(self.settings.schedule_update_time)
        self.timer.timeout.connect(lambda: asyncio.run(self.get_fake_schedule_data()))

    
    async def get_fake_schedule_data(self) -> None:
        with open('../response_1718131110455.json', 'rb') as json_file:
            data = json_file.read()
        self.refresh_schedule_table(data)

    
    async def get_schedule_data_from_API(self) -> None:
        self.timer.stop()
        request = QtNetwork.QNetworkRequest(API_URL+'get_scheduler')
        self.network_manager = QtNetwork.QNetworkAccessManager()
        self.network_manager.finished.connect(self.refresh_schedule_table, args=(self.network_manager.readAll(), self.network_manager.error()))
        self.network_manager.get(request)


    def refresh_schedule_table(self, data, error=QtNetwork.QNetworkReply.NetworkError.NoError):
        if error == QtNetwork.QNetworkReply.NetworkError.NoError:
            lang_status = ('✖', '✔')
            self.schedule_data = []
            bytes_string = data
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
        self.current_row_id = self.main_table.model().index(self.main_table.currentIndex().row(), 0).data()

    def set_active_row(self) -> None:
        if self.current_row_id:
            for row in range(self.main_table.model().rowCount()):
                index = self.main_table.model().index(row, 0)
                if index.data() == self.current_row_id:
                    self.main_table.setCurrentIndex(index)
                    return
    

    def __get_schedule_id_from_table_by_index(self, row_index: int, column_index: int=0) -> int:
        return self.main_table.model().index(row_index, column_index).data()

    def append_to_playlist(self) -> None:
        current_row = self.main_table.currentIndex().row()
        if current_row == -1: 
            raise SpeakerException("Ошибка воспроизведения", "Чтобы добавить объявление в очередь воспроизведения, его нужно выбрать.")
        schedule_id = self.__get_schedule_id_from_table_by_index(current_row)
        schedule = (list(filter(lambda data: data.get('schedule_id') == schedule_id, self.schedule_data_origin)))[0]
        languages_sorted = dict(sorted(schedule.get('languages').items(), key=lambda item: item[1].get('order', 0)))
        for key, language in languages_sorted.items():
            if language.get('display'):
                id = '_'.join((schedule_id, key))
                duration = ':'.join(map(lambda x: str(x) if x > 9 else '0'+str(x), divmod(int(round(language.get('duration'))), 60)))
                self.playlist.append((id, schedule.get('flight_number_full'), schedule.get('direction'), schedule.get('audio_text'), language.get('text'), duration, None))
                self.playlist_table_model.setItems(self.playlist[-1])

    def play_sound(self) -> None:
        if self.playlist:
            self.audio_trigger.stop()
            self.audio_trigger.set_audio_file('C:/PythonProjects/airport/modules/speaker/audio_files/'+self.playlist[0]+'.wav')
            self.audio_trigger.set_devices(self.settings)
            self.audio_trigger.start()
        else:
            raise SpeakerException("Ошибка воспроизведения", "Чтобы проиграть объявление, его нужно добавить в очередь.")
    
    def play_next(self) -> None:
        self.playlist.pop(0)
        if self.playlist:
            self.play_sound()
        
            
    def open_window_settings(self):
        pass

    def open_window_sound_add(self):
        pass
