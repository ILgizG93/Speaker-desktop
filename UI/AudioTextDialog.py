import json

from PySide6.QtWidgets import QGridLayout, QLabel, QDialog, QComboBox
from PySide6.QtCore import Qt, Slot, QUrl
from PySide6.QtGui import QIcon, QStandardItemModel, QStandardItem
from PySide6 import QtNetwork

from .AudioTextTable import AudioTextTable
from .Font import RobotoFont

class AudioTextDialog(QDialog):
    def __init__(self, parent, settings):
        super().__init__(parent)

        self.settings = settings

        self.setWindowTitle("Добавление объявлений")
        self.setWindowIcon(QIcon("icons/app/icon.png"))
        self.setFixedSize(1024, 700)

        self.layout = QGridLayout(self)
        
        self.flight_label = QLabel("Укажите рейс")
        self.flight_list_model = QStandardItemModel()
        self.flight_list = QComboBox()

        self.flight_label.setFixedWidth(120)
        self.flight_label.setFixedHeight(20)
        self.flight_list.setFixedWidth(170)
        self.flight_list.setFixedHeight(20)
        self.flight_list.setCursor(Qt.CursorShape.PointingHandCursor)

        self.flight_list.currentIndexChanged[int].connect(self.updateAudioTextList)
        self.flight_list.setModel(self.flight_list_model)

        self.audio_text_header = ('', 'Текст объявления', 'Зоны по умолчанию', 'Описание')
        self.audio_text_table = AudioTextTable(header=self.audio_text_header)
        # self.audio_text_table.selectionModel().selectionChanged.connect(self.get_current_sound)

        font = RobotoFont()
        self.flight_label.setFont(font.get_font())
        self.flight_list.setFont(font.get_font())
        self.audio_text_table.setFont(font.get_font())

        self.layout.addWidget(self.flight_label, 0, 0, alignment=Qt.AlignmentFlag.AlignTop)
        self.layout.addWidget(self.flight_list, 0, 1, alignment=Qt.AlignmentFlag.AlignTop)
        self.layout.addWidget(self.audio_text_table, 0, 2, 1, 4)

    async def get_flights_from_API(self) -> None:
        url_file = QUrl(self.settings.api_url+'get_flights')
        request = QtNetwork.QNetworkRequest(url_file)
        self.API_manager = QtNetwork.QNetworkAccessManager()
        self.API_manager.get(request)
        self.API_manager.finished.connect(self.refresh_flight_list)

    def refresh_flight_list(self, data: QtNetwork.QNetworkReply):
        if data.error() == QtNetwork.QNetworkReply.NetworkError.NoError:
            bytes_string = data.readAll()
            self.flight_data_origin = json.loads(str(bytes_string, 'utf-8'))
            if (len(self.flight_data_origin) == 0):
                self.flight_list_model.clear()
            else:
                for flight in self.flight_data_origin:
                    item = QStandardItem(f"{flight.get('flight_time')}      {flight.get('flight_number_full')}")
                    item.setData(flight)
                    self.flight_list_model.appendRow(item)
            print('Flight data refreshed!')

    async def get_audio_text_from_API(self) -> None:
        url_file = QUrl(self.settings.api_url+'get_audio_text')
        request = QtNetwork.QNetworkRequest(url_file)
        self.API_audio_manager = QtNetwork.QNetworkAccessManager()
        self.API_audio_manager.get(request)
        self.API_audio_manager.finished.connect(self.refresh_audio_text_table)

    def refresh_audio_text_table(self, data: QtNetwork.QNetworkReply):
        if data.error() == QtNetwork.QNetworkReply.NetworkError.NoError:
            self.audio_text_data = []
            bytes_string = data.readAll()
            self.audio_text_data_origin = json.loads(str(bytes_string, 'utf-8'))
            for data in self.audio_text_data_origin:
                self.audio_text_data.append((data.get('id'), data.get('name'), ', '.join(map(str, data.get('zones'))), data.get('description')))
            if (len(self.audio_text_data) == 0):
                self.audio_text_data = [(None,) * 4]
            self.audio_text_table.table_model.setItems(self.audio_text_data)
            # self.schedule_table.sortByColumn(*current_sort)
            print('Background data refreshed!')

    @Slot(int)
    def updateAudioTextList(self, row):
        it = self.flight_list_model.item(row)
        direction_id = it.data().get('direction_id')
        current_data = list(filter(lambda d: d.get('direction_id') == direction_id, self.audio_text_data_origin))
        current_data = list(map(lambda data: (data.get('id'), data.get('name'), ', '.join(map(str, data.get('zones'))), data.get('description')), current_data))
        self.audio_text_table.table_model.setItems(current_data)
