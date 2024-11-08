import json

from PySide6.QtWidgets import QVBoxLayout, QGridLayout, QLabel, QDialog, QComboBox, QGroupBox, QTimeEdit
from PySide6.QtCore import Qt, Slot, QUrl, QJsonDocument, Signal, QTime
from PySide6.QtGui import QIcon, QStandardItemModel, QStandardItem
from PySide6 import QtNetwork

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
        self.flight_label.setFixedSize(120, 20)

        self.flight_combobox_model = QStandardItemModel()
        self.flight_combobox = QComboBox()
        self.flight_combobox.setFixedSize(170, 20)
        self.flight_combobox.setCursor(Qt.CursorShape.PointingHandCursor)
        self.flight_combobox.currentIndexChanged[int].connect(self.display_flight_info)
        self.flight_combobox.setModel(self.flight_combobox_model)

        self.audio_text_reason_combobox_model = QStandardItemModel()
        self.audio_text_reason_combobox = QComboBox()
        self.audio_text_reason_combobox.setCursor(Qt.CursorShape.PointingHandCursor)
        self.audio_text_reason_combobox.setModel(self.audio_text_reason_combobox_model)

        self.terminal_combobox_model = QStandardItemModel()
        self.terminal_combobox = QComboBox()
        self.terminal_combobox.setCursor(Qt.CursorShape.PointingHandCursor)
        self.terminal_combobox.setModel(self.terminal_combobox_model)

        self.event_time = QTimeEdit()
        self.event_time.setTime(QTime.currentTime())

        self.audio_text_header = ('', 'Текст объявления', 'Зоны по умолчанию', 'Описание')
        self.audio_text_table = AudioTextTable(header=self.audio_text_header)
        self.audio_text_table.selectionModel().selectionChanged.connect(self.display_audio_text_info)
        self.audio_text_table.setFixedHeight(640)

        font = RobotoFont()
        self.flight_label.setFont(font.get_font())
        self.flight_combobox.setFont(font.get_font())
        self.audio_text_reason_combobox.setFont(font.get_font())
        self.terminal_combobox.setFont(font.get_font())
        self.event_time.setFont(font.get_font())
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
        self.audio_text_groupbox.setFixedHeight(300)

        self.additional_layout = QVBoxLayout()
        self.additional_groupbox = QGroupBox()
        self.additional_groupbox.setTitle('')
        self.additional_layout.addWidget(self.audio_text_reason_combobox)
        self.additional_layout.addWidget(self.terminal_combobox)
        self.additional_layout.addWidget(self.event_time)
        self.additional_groupbox.setLayout(self.additional_layout)
        self.additional_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

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
        self.layout.addWidget(self.audio_text_groupbox, 2, 4, 1, 1, alignment=Qt.AlignmentFlag.AlignTop)
        self.layout.addWidget(self.additional_groupbox, 3, 4, 1, 1, alignment=Qt.AlignmentFlag.AlignTop)
        self.layout.addWidget(self.btn_sound_append, 4, 4, 1, 1, alignment=Qt.AlignmentFlag.AlignBottom)
        self.layout.addWidget(self.btn_sound_close, 4, 4, 1, 1, alignment=Qt.AlignmentFlag.AlignBottom|Qt.AlignmentFlag.AlignRight)

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
                # item = QStandardItem("Вне рейса")
                # item.setData({'direction_id': None})
                # self.flight_combobox_model.appendRow(item)
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
        self.API_audio_text_manager = QtNetwork.QNetworkAccessManager()
        self.API_audio_text_manager.get(request)
        self.API_audio_text_manager.finished.connect(self.refresh_audio_text_table)

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
        if flight.data().get('direction_id'):
            if data.get('is_has_avia') is True and flight.data().get('is_has_avia') is False:
                return False
            if data.get('id') in flight.data().get('audio_text_id_list'):
                return True
        else:
            if data.get('direction_id') is None:
                return True

    async def get_audio_text_reasons_from_API(self) -> None:
        url_file = QUrl(settings.api_url+'get_audio_text_reasons')
        request = QtNetwork.QNetworkRequest(url_file)
        self.API_audio_text_reason_manager = QtNetwork.QNetworkAccessManager()
        self.API_audio_text_reason_manager.get(request)
        self.API_audio_text_reason_manager.finished.connect(self.refresh_audio_text_reasons_list)

    def refresh_audio_text_reasons_list(self, result: QtNetwork.QNetworkReply):
        match result.error():
            case QtNetwork.QNetworkReply.NetworkError.NoError:
                bytes_string = result.readAll()
                self.audio_text_reason_data_origin = json.loads(str(bytes_string, 'utf-8'))
                item = QStandardItem("Выберите причину задержки")
                self.audio_text_reason_combobox_model.appendRow(item)
                for audio_text_reason in self.audio_text_reason_data_origin:
                    audio_text_reason: dict
                    item = QStandardItem(f"{audio_text_reason.get('name')}")
                    item.setData(audio_text_reason)
                    self.audio_text_reason_combobox_model.appendRow(item)
                self.audio_text_reason_combobox_model.item(0).setEnabled(False)
                logger.info('Данные причин объявлений получены')

            case QtNetwork.QNetworkReply.NetworkError.ConnectionRefusedError:
                error_message = f"Данные причин объявлений не получены. Ошибка подключения к API: {result.errorString()}"
                self.open_message_dialog(error_message)
                logger.error(error_message)

    async def get_terminal_from_API(self) -> None:
        url_file = QUrl(settings.api_url+'get_terminals')
        request = QtNetwork.QNetworkRequest(url_file)
        self.terminal_manager = QtNetwork.QNetworkAccessManager()
        self.terminal_manager.get(request)
        self.terminal_manager.finished.connect(self.refresh_terminal_list)

    def refresh_terminal_list(self, result: QtNetwork.QNetworkReply):
        match result.error():
            case QtNetwork.QNetworkReply.NetworkError.NoError:
                bytes_string = result.readAll()
                self.terminal_data_origin = json.loads(str(bytes_string, 'utf-8'))
                item = QStandardItem("Выберите терминал")
                self.terminal_combobox_model.appendRow(item)
                for terminal in self.terminal_data_origin:
                    terminal: dict
                    item = QStandardItem(f"{terminal.get('name')}")
                    item.setData(terminal)
                    self.terminal_combobox_model.appendRow(item)
                self.terminal_combobox_model.item(0).setEnabled(False)
                logger.info('Данные терминалов получены')

            case QtNetwork.QNetworkReply.NetworkError.ConnectionRefusedError:
                error_message = f"Данные терминалов не получены. Ошибка подключения к API: {result.errorString()}"
                self.open_message_dialog(error_message)
                logger.error(error_message)

    @Slot(int)
    def display_flight_info(self, row):
        flight: QStandardItem = self.flight_combobox_model.item(row)
        direction_id: int = flight.data().get('direction_id')
        current_data: list = list(filter(self.get_filtered_audio_text, self.audio_text_data_origin))
        # current_data: list = list(filter(lambda d: d.get('direction_id') == direction_id, self.audio_text_data_origin))

        if direction_id:
            self.flight_info_layout.itemAt(0).widget().setText(f"Время рейса: {flight.data().get('plan_flight_time')}")
            self.flight_info_layout.itemAt(1).widget().setText(f"Направление: {flight.data().get('direction')}")
            if direction_id == 1:
                self.flight_info_layout.itemAt(2).widget().setText(f"Маршрут: {flight.data().get('airport_to')}")
            else:
                self.flight_info_layout.itemAt(2).widget().setText(f"Маршрут: {flight.data().get('airport_from')}")
            self.flight_info_layout.itemAt(3).widget().setText(f"Терминал: {flight.data().get('terminal')[0]}")
            self.flight_info_layout.itemAt(4).widget().setText(f"Выходы: {','.join(flight.data().get('boarding_gates')) if flight.data().get('boarding_gates') else ''}")
        else:
            self.flight_info_layout.itemAt(0).widget().setText("")
            self.flight_info_layout.itemAt(1).widget().setText("")
            self.flight_info_layout.itemAt(2).widget().setText("")
            self.flight_info_layout.itemAt(3).widget().setText("")
            self.flight_info_layout.itemAt(4).widget().setText("")

        current_data: list = list(map(lambda data: (data.get('id'), data.get('name'), ', '.join(map(str, data.get('zones'))), data.get('description')), current_data))
        self.audio_text_table.table_model.setItems(current_data)
        self.audio_text_table.selectRow(0)
        self.btn_sound_append.setEnabled(True)
        self.btn_sound_close.setEnabled(True)

    def get_current_audio_text(self):
        row_id: int = self.audio_text_table.get_current_row_id()
        current_data: dict = list(filter(lambda d: d.get('id') == row_id, self.audio_text_data_origin))[0]
        return current_data

    def display_audio_text_info(self):
        current_data: dict = self.get_current_audio_text()
        self.audio_text_info_layout.itemAt(0).widget().setText(current_data.get('annotation'))
        if current_data.get('is_has_reason'):
            self.audio_text_reason_combobox.setVisible(True)
        else:
            self.audio_text_reason_combobox.setHidden(True)
        if current_data.get('is_has_terminal'):
            self.terminal_combobox.setVisible(True)
        else:
            self.terminal_combobox.setHidden(True)
        if current_data.get('is_has_event_time'):
            self.event_time.setVisible(True)
        else:
            self.event_time.setHidden(True)

    def open_message_dialog(self, message: str) -> None:
        self.message_dialog: MessageDialog = MessageDialog(self, message)
        self.message_dialog.exec()

    def append_audio_text_to_schedule(self) -> None:
        reason_id: int = None
        terminal: str = None
        event_time: str = None
        current_data: dict = self.get_current_audio_text()

        if current_data.get('is_has_reason'):
            reason_indx: int = self.audio_text_reason_combobox.currentIndex()
            reason_item: QStandardItem = self.audio_text_reason_combobox_model.item(reason_indx)
            reason_data: dict = reason_item.data()
            if reason_data is None:
                error_message: str = f"Ошибка добавления объявления: Необходимо выбрать причину задержки"
                logger.error(error_message)
                self.open_message_dialog(error_message)
                return
            reason_id = reason_data.get('id')

        if current_data.get('is_has_terminal'):
            terminal_indx: int = self.terminal_combobox.currentIndex()
            terminal_item: QStandardItem = self.terminal_combobox_model.item(terminal_indx)
            terminal_data: dict = terminal_item.data()
            if terminal_data is None:
                error_message: str = f"Ошибка добавления объявления: Необходимо выбрать терминал"
                logger.error(error_message)
                self.open_message_dialog(error_message)
                return
            terminal = terminal_data.get('name')

        if current_data.get('is_has_event_time'):
            event_time: str = self.event_time.text()

        flight_indx: int = self.flight_combobox.currentIndex()
        flight_item: QStandardItem = self.flight_combobox_model.item(flight_indx)
        flight_data: dict = flight_item.data()
        flight_id: int = flight_data.get('flight_id')
        audio_text_id: int = self.audio_text_table.get_current_row_id()
        
        url_file = QUrl(settings.api_url+'append_audio_text_to_schedule')
        self.body = {
            'flight_id': flight_id,
            'audio_text_id': audio_text_id,
            'audio_text_reason_id': reason_id,
            'terminal': terminal,
            'event_time': event_time
        }
        request = QtNetwork.QNetworkRequest(url_file)
        request.setHeader(QtNetwork.QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")
        self.API_post = QtNetwork.QNetworkAccessManager()
        self.API_post.post(request, QJsonDocument(self.body).toJson())
        self.API_post.finished.connect(self.after_append)

    def after_append(self, result: QtNetwork.QNetworkReply) -> None:
        match result.error():
            case QtNetwork.QNetworkReply.NetworkError.NoError:
                info_message = "Объявление добавлено"
                logger.info(info_message)
                reply = (200, info_message, self.body)

            case QtNetwork.QNetworkReply.NetworkError.ConnectionRefusedError:
                error_message = f"Данные не сохранены. Ошибка подключения к API: {result.errorString()}"
                logger.error(error_message)
                reply = (400, error_message, self.body)
            
            case _:
                error_message = "Ошибка при добавлении объявления"
                logger.error(error_message)
                reply = (500, error_message, self.body)
        self.append_signal.emit(reply)
    
    def closeEvent(self, event):
        self.append_signal.emit(None)
