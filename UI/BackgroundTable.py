import json
import asyncio

from PySide6.QtWidgets import QTableWidget, QHeaderView, QAbstractItemView, QWidget, QHBoxLayout, QTableWidgetItem, QCheckBox
from PySide6.QtCore import Qt, QUrl, QUrlQuery, QTimer, QJsonDocument, Signal
from PySide6 import QtNetwork

from globals import root_directory, settings, logger, TableCheckbox
from .Font import RobotoFont


class BackgroundTable(QTableWidget):
    current_audio_id: str = None
    current_data: dict = {}
    play_signal: Signal = Signal(QtNetwork.QNetworkReply)
    stop_signal: Signal = Signal(tuple)
    error_signal: Signal = Signal(str)

    def __init__(self, header: tuple[str], zones: dict, parent=None) -> None:
        self.header: tuple[str] = header
        self.zones: dict = zones
        self.col_count: int = len(self.header)
        self.row_count: int = 0
        self.is_autoplay: bool = False
        super().__init__(self.row_count, self.col_count, parent)

        self.font: RobotoFont = RobotoFont()

        self.setAlternatingRowColors(True)
        self.setMaximumWidth(500)
        self.verticalHeader().setHidden(True)

        self.setHorizontalHeaderLabels(self.header)
        self.setColumnHidden(0, True)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.setColumnWidth(2, 32)
        self.setColumnWidth(3, 32)
        self.setColumnWidth(4, 32)
        for i in range(0, len(self.zones)):
            self.horizontalHeader().setSectionResizeMode(5+i, QHeaderView.ResizeMode.Fixed)
            self.setColumnWidth(5+i, 32)

        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        self.timer = QTimer()
        self.timer.setInterval(settings.background_schedule_update_time*1000)
        self.timer.timeout.connect(lambda: asyncio.run(self.get_background_data_from_API()))

        from UI.SpeakerStatusBar import speaker_status_bar
        self.speaker_status_bar = speaker_status_bar

    async def get_background_data_from_API(self) -> None:
        self.timer.stop()
        url_file = QUrl(settings.api_url+'get_audio_background_text')
        request = QtNetwork.QNetworkRequest(url_file)
        self.API_bg_manager = QtNetwork.QNetworkAccessManager()
        self.API_bg_manager.get(request)
        self.API_bg_manager.finished.connect(self.refresh_background_table)

    def refresh_background_table(self, result: QtNetwork.QNetworkReply) -> None:
        match result.error():
            case QtNetwork.QNetworkReply.NetworkError.NoError:
                self.background_data = []
                bytes_string = result.readAll()
                self.data_origin: list[dict] = json.loads(str(bytes_string, 'utf-8'))
                for data in self.data_origin:
                    self.background_data.append((str(data.get('audio_text_id')), data.get('name'),
                        data.get('languages').get('RUS').get('display'),
                        data.get('languages').get('TAT').get('display'),
                        data.get('languages').get('ENG').get('display'),
                        *list(map(lambda i: True if i[0]+1 in data.get('zones_list') else False, enumerate(self.zones)))
                    ))
                if (len(self.background_data) == 0):
                    self.background_data = [(None,) * len(self.header)]
                    self.setRowCount(0)
                else:
                    self.setRowCount(len(self.background_data))
                    for row_indx, data in enumerate(self.background_data):
                        current_schedule_background: list = list(filter(lambda d: int(data[0]) == d.get('audio_text_id'), self.data_origin))
                        if len(current_schedule_background) > 0:
                            current_schedule_background: dict = current_schedule_background[0]
                            for col_indx, item in enumerate(data):
                                if col_indx in [i for i in range(5, 5+len(self.zones)+1)]:
                                    widget = QWidget()
                                    checkbox = TableCheckbox(row_indx, col_indx)
                                    checkbox.setChecked(item)
                                    checkbox.checkStateChanged.connect(self.on_checkbox_state_change)
                                    layoutH = QHBoxLayout(widget)
                                    layoutH.addWidget(checkbox)
                                    layoutH.setAlignment(Qt.AlignmentFlag.AlignCenter)
                                    self.setCellWidget(row_indx, col_indx, widget)
                                elif col_indx in [2,3,4] and item:
                                    widget = QWidget()
                                    layoutH = QHBoxLayout(widget)
                                    layoutH.setAlignment(Qt.AlignmentFlag.AlignCenter)
                                    if item:
                                        checkbox = TableCheckbox(row_indx, col_indx)
                                        checkbox.setChecked(col_indx-1 in current_schedule_background.get('languages_list'))
                                        checkbox.checkStateChanged.connect(self.on_checkbox_state_change)
                                        layoutH.addWidget(checkbox)
                                    self.setCellWidget(row_indx, col_indx, widget)
                                else:
                                    element = QTableWidgetItem(item)
                                    element.setFont(self.font.get_font())
                                    self.setItem(row_indx, col_indx, element)
                                self.resizeRowToContents(row_indx)
                info_message = "Фоновые объявления обновлены"
                self.speaker_status_bar.setStatusBarText(text=info_message)
                self.set_active_row()

            case QtNetwork.QNetworkReply.NetworkError.ConnectionRefusedError:
                error_message = f"Фоновые объявления. Ошибка подключения к API: {result.errorString()}"
                self.speaker_status_bar.setStatusBarText(text=error_message, is_error=True)

        self.timer.start()

    def get_current_row_id(self) -> str:
        try:
            row_id = self.item(self.currentRow(), 0).text()
        except AttributeError as err:
            return None
        return row_id

    def get_current_languages(self) -> list[int]:
        current_languages: list[int] = []
        row: int = self.currentRow()
        for i in range(2, 5):
            cell = self.cellWidget(row,i)
            if cell and cell.findChild(QCheckBox).checkState() == Qt.CheckState.Checked:
                current_languages.append(i-1)
        return current_languages

    def get_current_zones(self) -> list[int]:
        current_zones: list[int] = []
        row: int = self.currentRow()
        for i in range(self.col_count - len(self.zones), self.col_count):
            checkbox: QCheckBox = self.cellWidget(row,i).findChild(QCheckBox)
            if checkbox.checkState() == Qt.CheckState.Checked:
                current_zones.append(i-4)
        return current_zones

    def get_current_terminal(self) -> None:
        return None

    def get_current_boarding_gates(self) -> None:
        return None

    def get_current_row_data(self, row_id: str) -> dict:
        current_data = list(filter(lambda d: d.get('audio_text_id') == int(row_id), self.data_origin))
        if current_data:
            return current_data[0]
        elif self.data_origin:
            return self.data_origin[0]

    def set_active_schedule_id(self) -> None:
        row_id = self.get_current_row_id()
        if row_id:
            current_data = self.get_current_row_data(row_id)
            if current_data:
                self.current_audio_id = current_data.get('audio_text_id')
        else:
            self.current_audio_id = None

    def set_active_row(self) -> None:
        if self.current_data and self.current_data.get('audio_text_id'):
            if self.current_audio_id is None:
                self.set_active_schedule_id()
                self.selectRow(0)
            else:
                for row in range(self.model().rowCount()):
                    index = self.model().index(row, 0)
                    if int(index.data()) == self.current_audio_id:
                        self.setCurrentIndex(index)
                        return
        else:
            if self.data_origin:
                self.current_data = self.data_origin[0]
            self.selectRow(0)

    async def get_audio_file(self):
        row_id = self.get_current_row_id()
        if row_id is None:
            error_message: str = "Ошибка воспроизведения: Необходимо выбрать объявление"
            self.error_signal.emit(error_message)
            return

        self.current_data = self.get_current_row_data(row_id)
        self.current_sound_file = root_directory+'/'+settings.file_name
        self.current_audio_id = self.current_data.get('audio_text_id')

        if len(self.get_current_languages()) == 0:
            error_message: str = "Ошибка воспроизведения: Необходимо выбрать хотя бы один язык для воспроизведения"
            self.error_signal.emit(error_message)
            return

        self.timer.stop()

        url_file = QUrl(settings.api_url+'get_scheduler_background_sound')
        query = QUrlQuery()
        query.addQueryItem('audio_text_id', str(self.current_data.get('audio_text_id')))
        url_file.setQuery(query.query())

        request = QtNetwork.QNetworkRequest(url_file)
        self.API_manager = QtNetwork.QNetworkAccessManager()
        request.setHeader(QtNetwork.QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")
        body = QJsonDocument({'languages': self.get_current_languages(), 'zones': self.get_current_zones()})

        reply = self.API_manager.post(request, body.toJson())
        self.API_manager.finished.connect(lambda: self.play_signal.emit(reply))

    def update_schedule(self, is_deleted: bool = None) -> None:
        self.current_data = self.get_current_row_data(self.get_current_row_id())
        url_file = QUrl(settings.api_url+'update_schedule_background')
        request = QtNetwork.QNetworkRequest(url_file)
        request.setHeader(QtNetwork.QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")
        self.API_post = QtNetwork.QNetworkAccessManager()
        body = QJsonDocument({
            'audio_text_id': self.current_data.get('audio_text_id'),
            'languages': self.get_current_languages(), 
            'zones': self.get_current_zones()
        })
        self.API_post.post(request, body.toJson())
        self.API_post.finished.connect(self.after_update_schedule)

    def after_update_schedule(self, result: QtNetwork.QNetworkReply) -> None:
        match result.error():
            case QtNetwork.QNetworkReply.NetworkError.NoError:
                logger.info(f"Данные сохранены")

            case QtNetwork.QNetworkReply.NetworkError.ConnectionRefusedError:
                error_message = f"Данные не сохранены. Ошибка подключения к API: {result.errorString()}"
                self.speaker_status_bar.setStatusBarText(text=error_message, is_error=True)

    def delete_schedule(self) -> None:
        audio_text_id: int = self.current_data.get('audio_text_id')
        for row in reversed(range(self.model().rowCount())):
            indx = self.model().index(row, 0)
            if indx.data():
                row_audio_text_id = int(indx.data())
                if row_audio_text_id == audio_text_id:
                    self.removeRow(row)
            else:
                break

    def on_checkbox_state_change(self) -> None:
        row, column = map(int, self.sender().objectName().split('_'))
        self.selectRow(row)
        self.update_schedule()
