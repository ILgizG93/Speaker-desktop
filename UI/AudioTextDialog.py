import json

from PySide6.QtWidgets import QVBoxLayout, QGridLayout, QLabel, QDialog, QComboBox, QGroupBox
from PySide6.QtCore import Qt, Slot, QUrl, QUrlQuery, QJsonDocument, Signal
from PySide6.QtGui import QIcon, QStandardItemModel, QStandardItem
from PySide6 import QtNetwork

from typing import Optional
from globals import settings, logger
from .AudioTextTable import AudioTextTable
from .Font import RobotoFont
from .MessageDialog import MessageDialog
from .SpeakerButton import SpeakerButton

class AudioTextDialog(QDialog):
    append_signal: Signal = Signal(tuple)

    def __init__(self, parent):
        super().__init__(parent)

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

        self.btn_sound_append = SpeakerButton(text='Добавить')
        self.btn_sound_append.clicked.connect(self.append_audio_text_to_schedule)
        self.btn_sound_append.setDisabled(True)
        self.btn_sound_close = SpeakerButton(text='Закрыть')
        self.btn_sound_close.clicked.connect(self.close)
        self.btn_sound_close.setDisabled(True)
        
        self.layout.addWidget(self.flight_label, 0, 0, alignment=Qt.AlignmentFlag.AlignTop)
        self.layout.addWidget(self.flight_combobox, 0, 1, alignment=Qt.AlignmentFlag.AlignTop)
        self.layout.addWidget(self.audio_text_table, 1, 0, 4, 3)
        self.layout.addWidget(self.flight_info_groupbox, 1, 4, 1, 1, alignment=Qt.AlignmentFlag.AlignTop)
        self.layout.addWidget(self.audio_text_groupbox, 2, 4, 2, 1, alignment=Qt.AlignmentFlag.AlignTop)
        self.layout.addWidget(self.btn_sound_append, 3, 4, 2, 1, alignment=Qt.AlignmentFlag.AlignBottom)
        self.layout.addWidget(self.btn_sound_close, 3, 4, 2, 1, alignment=Qt.AlignmentFlag.AlignBottom|Qt.AlignmentFlag.AlignRight)

    async def get_flights_from_API(self, flight_id: int = None) -> None:
        self.current_flight_id = flight_id
        url_file = QUrl(settings.api_url+'get_flights')
        request = QtNetwork.QNetworkRequest(url_file)
        self.API_manager = QtNetwork.QNetworkAccessManager()
        self.API_manager.get(request)
        self.API_manager.finished.connect(self.refresh_flight_list)

    def refresh_flight_list(self, result: QtNetwork.QNetworkReply):
        match result.error():
            case QtNetwork.QNetworkReply.NetworkError.NoError:
                bytes_string = result.readAll()
                self.flight_data_origin = json.loads(str(bytes_string, 'utf-8'))
                for flight in self.flight_data_origin:
                    flight: dict
                    item = QStandardItem(f"{flight.get('plan_flight_time')}     {flight.get('flight_number_full')}")
                    item.setData(flight)
                    self.flight_combobox_model.appendRow(item)
                    if self.current_flight_id == flight.get('flight_id'):
                        self.flight_combobox.setCurrentIndex(self.flight_combobox_model.rowCount()-1)
                logger.info('Данные рейсов получены')

            case QtNetwork.QNetworkReply.NetworkError.ConnectionRefusedError:
                error_message = f"Данные рейсов не получены. Ошибка подключения к API: {result.errorString()}"
                self.open_message_dialog(error_message)
                logger.error(error_message)

    async def get_audio_text_from_API(self) -> None:
        url_file = QUrl(settings.api_url+'get_audio_text')
        request = QtNetwork.QNetworkRequest(url_file)
        self.API_audio_manager = QtNetwork.QNetworkAccessManager()
        self.API_audio_manager.get(request)
        self.API_audio_manager.finished.connect(self.refresh_audio_text_table)

    def refresh_audio_text_table(self, result: QtNetwork.QNetworkReply):
        match result.error():
            case QtNetwork.QNetworkReply.NetworkError.NoError:
                self.audio_text_data = []
                bytes_string = result.readAll()
                self.audio_text_data_origin = json.loads(str(bytes_string, 'utf-8'))
                for data in self.audio_text_data_origin:
                    data: dict
                    self.audio_text_data.append((data.get('id'), data.get('name'), ', '.join(map(str, data.get('zones'))), data.get('description')))
                if (len(self.audio_text_data) == 0):
                    self.audio_text_data = [(None,) * 4]
                # self.audio_text_table.table_model.setItems(self.audio_text_data)
                logger.info('Данные объявлений получены')

            case QtNetwork.QNetworkReply.NetworkError.ConnectionRefusedError:
                error_message = f"Данные объявлений не получены. Ошибка подключения к API: {result.errorString()}"
                self.open_message_dialog(error_message)
                logger.error(error_message)

    def get_filtered_audio_text(self, data: dict):
        row: int = self.flight_combobox.currentIndex()
        flight: QStandardItem = self.flight_combobox_model.item(row)
        if data.get('id') in flight.data().get('audio_text_id_list'):
            return True

    @Slot(int)
    def display_flight_info(self, row):
        flight: QStandardItem = self.flight_combobox_model.item(row)
        direction_id: int = flight.data().get('direction_id')
        current_data: list = list(filter(self.get_filtered_audio_text, self.audio_text_data_origin))
        # current_data: list = list(filter(lambda d: d.get('direction_id') == direction_id, self.audio_text_data_origin))

        self.flight_info_layout.itemAt(0).widget().setText(f"Время рейса: {flight.data().get('plan_flight_time')}")
        self.flight_info_layout.itemAt(1).widget().setText(f"Направление: {flight.data().get('direction')}")
        if direction_id == 1:
            self.flight_info_layout.itemAt(2).widget().setText(f"Маршрут: {flight.data().get('airport_to')}")
        else:
            self.flight_info_layout.itemAt(2).widget().setText(f"Маршрут: {flight.data().get('airport_from')}")
        self.flight_info_layout.itemAt(3).widget().setText(f"Терминал: {flight.data().get('terminal')[0]}")
        self.flight_info_layout.itemAt(4).widget().setText(f"Выходы: {','.join(flight.data().get('boarding_gates')) if flight.data().get('boarding_gates') else ''}")

        current_data: list = list(map(lambda data: (data.get('id'), data.get('name'), ', '.join(map(str, data.get('zones'))), data.get('description')), current_data))
        self.audio_text_table.table_model.setItems(current_data)
        self.audio_text_table.selectRow(0)
        self.btn_sound_append.setEnabled(True)
        self.btn_sound_close.setEnabled(True)

    def display_audio_text_info(self):
        row_id: int = self.audio_text_table.get_current_row_id()
        current_data: list = list(filter(lambda d: d.get('id') == row_id, self.audio_text_data_origin))[0]
        self.audio_text_info_layout.itemAt(0).widget().setText(current_data.get('annotation'))

    def open_message_dialog(self, message: str) -> None:
        self.message_dialog: MessageDialog = MessageDialog(self, message)
        self.message_dialog.exec()

    def append_audio_text_to_schedule(self) -> None:
        flight_indx: int = self.flight_combobox.currentIndex()
        flight_item: QStandardItem = self.flight_combobox_model.item(flight_indx)
        flight_data: dict = flight_item.data()
        flight_id: int = flight_data.get('flight_id')
        audio_text_id: int = self.audio_text_table.get_current_row_id()
        
        url_file = QUrl(settings.api_url+'append_audio_text_to_schedule')
        query = QUrlQuery()
        query.addQueryItem('flight_id', str(flight_id))
        query.addQueryItem('audio_text_id', str(audio_text_id))
        url_file.setQuery(query.query())
        self.body = {
            'flight_id': flight_id,
            'audio_text_id': audio_text_id
        }
        request = QtNetwork.QNetworkRequest(url_file)
        request.setHeader(QtNetwork.QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")
        self.API_post = QtNetwork.QNetworkAccessManager()
        self.API_post.post(request, QJsonDocument().toJson())
        self.API_post.finished.connect(self.after_append)

    def after_append(self, result: QtNetwork.QNetworkReply) -> None:
        match result.error():
            case QtNetwork.QNetworkReply.NetworkError.NoError:
                bytes_string = result.readAll()
                response: int = json.loads(str(bytes_string, 'utf-8'))
                if response == 200:
                    info_message = "Объявление добавлено"
                    logger.info(info_message)
                    reply = (response, info_message, self.body)
                else:
                    error_message = "Ошибка при добавлении объявления"
                    logger.error(error_message)
                    reply = (response, error_message, self.body)

            case QtNetwork.QNetworkReply.NetworkError.ConnectionRefusedError:
                error_message = f"Данные не сохранены. Ошибка подключения к API: {result.errorString()}"
                logger.error(error_message)
                reply = (400, error_message)
        self.append_signal.emit(reply)
    
    def closeEvent(self, event):
        self.append_signal.emit(None)
