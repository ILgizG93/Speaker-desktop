import json

from PySide6.QtWidgets import QVBoxLayout, QGridLayout, QLabel, QDialog, QComboBox, QWidget, QGroupBox
from PySide6.QtCore import Qt, Slot, QUrl
from PySide6.QtGui import QIcon, QStandardItemModel, QStandardItem
from PySide6 import QtNetwork

from settings import SpeakerSetting
from .AudioTextTable import AudioTextTable
from .Font import RobotoFont

class AudioTextDialog(QDialog):
    def __init__(self, parent, settings):
        super().__init__(parent)

        self.settings: SpeakerSetting = settings

        self.setWindowTitle("Добавление объявлений")
        self.setWindowIcon(QIcon("icons/app/icon.png"))
        self.setFixedSize(1024, 700)

        self.layout: QGridLayout = QGridLayout(self)
        
        self.flight_label = QLabel("Укажите рейс")
        self.flight_combobox_model = QStandardItemModel()
        self.flight_combobox = QComboBox()

        self.flight_label.setFixedWidth(120)
        self.flight_label.setFixedHeight(20)
        self.flight_combobox.setFixedWidth(170)
        self.flight_combobox.setFixedHeight(20)
        self.flight_combobox.setCursor(Qt.CursorShape.PointingHandCursor)

        self.flight_combobox.currentIndexChanged[int].connect(self.display_flight_info)
        self.flight_combobox.setModel(self.flight_combobox_model)

        self.audio_text_header = ('', 'Текст объявления', 'Зоны по умолчанию', 'Описание')
        self.audio_text_table = AudioTextTable(header=self.audio_text_header)
        self.audio_text_table.selectionModel().selectionChanged.connect(self.display_audio_text_info)
        self.audio_text_table.setFixedHeight(640)

        font = RobotoFont()
        self.flight_label.setFont(font.get_font())
        self.flight_combobox.setFont(font.get_font())
        self.audio_text_table.setFont(font.get_font())

        self.flight_info_layout = QVBoxLayout()
        self.flight_info_layout.addWidget(QLabel(f"Время рейса:"))
        self.flight_info_layout.itemAt(0).widget().setFont(font.get_font())
        self.flight_info_layout.addWidget(QLabel(f"Направление:"))
        self.flight_info_layout.itemAt(1).widget().setFont(font.get_font())
        self.flight_info_layout.addWidget(QLabel(f"Маршрут:"))
        self.flight_info_layout.itemAt(2).widget().setFont(font.get_font())
        self.flight_info_layout.addWidget(QLabel(f"Терминал:"))
        self.flight_info_layout.itemAt(3).widget().setFont(font.get_font())
        self.flight_info_layout.addWidget(QLabel(f"Выходы:"))
        self.flight_info_layout.itemAt(4).widget().setFont(font.get_font())

        self.flight_info_groupbox = QGroupBox()
        self.flight_info_groupbox.setTitle('Информация о рейсе')
        self.flight_info_groupbox.setLayout(self.flight_info_layout)

        self.audio_text_info_layout = QVBoxLayout()
        label = QLabel()
        label.setWordWrap(True)
        label.setFont(font.get_font())
        label.setFixedWidth(320)
        label.setAlignment(Qt.AlignmentFlag.AlignJustify)
        self.audio_text_groupbox = QGroupBox()
        self.audio_text_groupbox.setTitle('Аннотация')
        self.audio_text_info_layout.addWidget(label)
        self.audio_text_groupbox.setLayout(self.audio_text_info_layout)
        
        self.layout.addWidget(self.flight_label, 0, 0, alignment=Qt.AlignmentFlag.AlignTop)
        self.layout.addWidget(self.flight_combobox, 0, 1, alignment=Qt.AlignmentFlag.AlignTop)
        self.layout.addWidget(self.audio_text_table, 1, 0, 3, 3)
        self.layout.addWidget(self.flight_info_groupbox, 1, 4, 1, 1, alignment=Qt.AlignmentFlag.AlignTop)
        self.layout.addWidget(self.audio_text_groupbox, 2, 4, 2, 1, alignment=Qt.AlignmentFlag.AlignTop)

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
                self.flight_combobox_model.clear()
            else:
                for flight in self.flight_data_origin:
                    item = QStandardItem(f"{flight.get('plan_flight_time')}      {flight.get('flight_number_full')}")
                    item.setData(flight)
                    self.flight_combobox_model.appendRow(item)
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
            print('Background data refreshed!')

    @Slot(int)
    def display_flight_info(self, row):
        it = self.flight_combobox_model.item(row)
        direction_id = it.data().get('direction_id')
        current_data = list(filter(lambda d: d.get('direction_id') == direction_id, self.audio_text_data_origin))

        self.flight_info_layout.itemAt(0).widget().setText(f"Время рейса: {it.data().get('plan_flight_time')}")
        self.flight_info_layout.itemAt(1).widget().setText(f"Направление: {it.data().get('direction')}")
        if direction_id == 1:
            self.flight_info_layout.itemAt(2).widget().setText(f"Маршрут: {it.data().get('airport_to')}")
        else:
            self.flight_info_layout.itemAt(2).widget().setText(f"Маршрут: {it.data().get('airport_from')}")
        self.flight_info_layout.itemAt(3).widget().setText(f"Терминал: {it.data().get('terminal')[0]}")
        self.flight_info_layout.itemAt(4).widget().setText(f"Выходы: {','.join(it.data().get('boarding_gates')) if it.data().get('boarding_gates') else ''}")

        current_data = list(map(lambda data: (data.get('id'), data.get('name'), ', '.join(map(str, data.get('zones'))), data.get('description')), current_data))
        self.audio_text_table.table_model.setItems(current_data)

    def display_audio_text_info(self):
        row_id = self.audio_text_table.model().index(self.audio_text_table.currentIndex().row(), 0).data()
        current_data = list(filter(lambda d: d.get('id') == row_id, self.audio_text_data_origin))[0]
        self.audio_text_info_layout.itemAt(0).widget().setText(current_data.get('annotation'))
