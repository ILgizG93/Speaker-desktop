import json
import asyncio

from typing import Optional
from PySide6.QtWidgets import QTableWidget, QHeaderView, QAbstractItemView, QTableWidgetItem, QWidget, QCheckBox, QHBoxLayout, QStatusBar
from PySide6.QtCore import Qt, QUrl, QTimer, QJsonDocument
from PySide6 import QtNetwork

from globals import settings, logger
from .Font import RobotoFont

class TableCheckbox(QCheckBox):
    def __init__(self, row_indx, col_indx):
        super().__init__()        
        self.setObjectName(f'{row_indx}_{col_indx}')
        self.setStyleSheet("QCheckBox::indicator" "{" "width :20px;" "height : 20px;" "}")
        self.setFixedWidth(22)
        self.setFixedHeight(32)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

class ScheduleTable(QTableWidget):
    def __init__(self, header: tuple[str], zones: dict, parent=None) -> None:
        self.header: tuple[str] = header
        self.zones: dict = zones
        self.col_count: int = len(self.header)
        self.row_count: int = 0
        super().__init__(self.row_count, self.col_count, parent)

        self.font: RobotoFont = RobotoFont()
        self.current_schedule_id: str = None
        self.current_flight: dict = {}

        self.speaker_status_bar = QStatusBar()

        self.setMinimumWidth(300)
        
        self.setHorizontalHeaderLabels(self.header)
        self.setColumnHidden(0, True)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        self.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        self.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)
        self.horizontalHeader().setSectionResizeMode(8, QHeaderView.ResizeMode.Fixed)
        self.horizontalHeader().setSectionResizeMode(9, QHeaderView.ResizeMode.Fixed)
        self.horizontalHeader().setSectionResizeMode(10, QHeaderView.ResizeMode.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(11, QHeaderView.ResizeMode.ResizeToContents)
        self.setColumnWidth(7, 32)
        self.setColumnWidth(8, 32)
        self.setColumnWidth(9, 32)
        for i in range(0, len(self.zones)):
            self.horizontalHeader().setSectionResizeMode(12+i, QHeaderView.ResizeMode.Fixed)
            self.setColumnWidth(12+i, 32)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        
        self.timer = QTimer()
        self.timer.setInterval(settings.schedule_update_time)
        self.timer.timeout.connect(lambda: asyncio.run(self.get_scheduler_data_from_API()))

        from .SpeakerStatusBar import speaker_status_bar
        self.speaker_status_bar = speaker_status_bar
    
    async def get_scheduler_data_from_API(self) -> None:
        self.timer.stop()
        url_file = QUrl(settings.api_url+'get_scheduler')
        request = QtNetwork.QNetworkRequest(url_file)
        self.API_manager = QtNetwork.QNetworkAccessManager()
        self.API_manager.get(request)
        self.API_manager.finished.connect(self.refresh_schedule_table)

    def refresh_schedule_table(self, result: QtNetwork.QNetworkReply) -> None:
        match result.error():
            case QtNetwork.QNetworkReply.NetworkError.NoError:
                self.schedule_data = []
                bytes_string = result.readAll()
                self.schedule_data_origin = json.loads(str(bytes_string, 'utf-8'))
                for data in self.schedule_data_origin:
                    self.schedule_data.append((
                        data.get('schedule_id'), data.get('flight_number_full'), data.get('direction'), data.get('plan_flight_time'), data.get('public_flight_time'), 
                        data.get('audio_text'), data.get('airport'),
                        data.get('languages').get('RUS').get('display'),
                        data.get('languages').get('TAT').get('display'),
                        data.get('languages').get('ENG').get('display'), 
                        data.get('terminal'), data.get('boarding_gates'),
                        *list(map(lambda i: True if i[0]+1 in data.get('zones_list') else False, enumerate(self.zones)))
                    ))
                if (len(self.schedule_data) == 0):
                    self.schedule_data = [(None,) * len(self.header)]

                if (len(self.schedule_data) == 0):
                    self.setRowCount(0)
                else:
                    self.setRowCount(len(self.schedule_data))
                    for row_indx, data in enumerate(self.schedule_data):
                        current_schedule: list = list(filter(lambda d: data[0] == d.get('schedule_id'), self.schedule_data_origin))
                        if len(current_schedule) > 0:
                            current_schedule: dict = current_schedule[0]
                            for col_indx, item in enumerate(data):
                                if col_indx in [2,3,4,10,11]:
                                    element = QTableWidgetItem(item)
                                    element.setFont(self.font.get_font())
                                    element.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                                    self.setItem(row_indx, col_indx, element)
                                elif col_indx in [i for i in range(11, 11+len(self.zones)+1)]:
                                    widget = QWidget()
                                    checkbox = TableCheckbox(row_indx, col_indx)
                                    # if current_schedule.get('flight_type_id') in self.zones[col_indx-12].get('flight_type'):
                                    checkbox.setChecked(item)
                                    checkbox.checkStateChanged.connect(self.on_checkbox_state_change)
                                    layoutH = QHBoxLayout(widget)
                                    layoutH.addWidget(checkbox)
                                    layoutH.setAlignment(Qt.AlignmentFlag.AlignCenter)
                                    layoutH.setContentsMargins(0, 0, 0, 0)
                                    self.setCellWidget(row_indx, col_indx, widget)
                                elif col_indx in [7,8,9] and item:
                                    widget = QWidget()
                                    checkbox = TableCheckbox(row_indx, col_indx)
                                    checkbox.setChecked(col_indx-6 in current_schedule.get('languages_list'))
                                    checkbox.checkStateChanged.connect(self.on_checkbox_state_change)
                                    layoutH = QHBoxLayout(widget)
                                    layoutH.addWidget(checkbox)
                                    layoutH.setAlignment(Qt.AlignmentFlag.AlignHCenter)
                                    layoutH.setContentsMargins(0, 0, 0, 15)
                                    self.setCellWidget(row_indx, col_indx, widget)
                                else:
                                    element = QTableWidgetItem(item)
                                    element.setFont(self.font.get_font())
                                    self.setItem(row_indx, col_indx, element)
                        else:
                            self.removeRow(0)
                info_message = "Данные обновлены"
                self.speaker_status_bar.setStatusBarText(text=info_message)
                self.current_flight = self.get_current_flight(self.get_current_row_id())
                self.set_active_row()

            case QtNetwork.QNetworkReply.NetworkError.ConnectionRefusedError:
                error_message = f"Данные не обновлены. Ошибка подключения к API: {result.errorString()}"
                self.speaker_status_bar.setStatusBarText(text=error_message, is_error=True)

        self.timer.start()

    def get_current_row_id(self) -> str:
        try:
            row_id = self.item(self.currentRow(), 0).text()
        except AttributeError as err:
            return None
        return row_id
    
    def get_current_flight(self, row_id: str) -> dict:
        current_flight = list(filter(lambda d: d.get('schedule_id') == row_id, self.schedule_data_origin))
        if current_flight:
            return current_flight[0]
        elif self.schedule_data_origin:
            return self.schedule_data_origin[0]

    def set_active_row(self) -> None:
        if self.current_flight and self.current_flight.get('schedule_id'):
            if self.current_schedule_id is None:
                self.current_schedule_id = self.current_flight.get('schedule_id')
            for row in range(self.model().rowCount()):
                index = self.model().index(row, 0)
                if index.data() == self.current_schedule_id:
                    self.setCurrentIndex(index)
                    return
            self.selectRow(0)
        else:
            if self.schedule_data_origin:
                self.current_flight = self.schedule_data_origin[0]
            self.selectRow(0)
    
    def get_current_languages(self) -> list[int]:
        current_languages: list[int] = []
        row: int = self.currentRow()
        for i in range(7, 10):
            cell = self.cellWidget(row,i)
            if cell and cell.findChild(QCheckBox).checkState() == Qt.CheckState.Checked:
                current_languages.append(i-6)
        return current_languages
    
    def get_current_zones(self) -> list[int]:
        current_zones: list[int] = []
        row: int = self.currentRow()
        for i in range(self.col_count - len(self.zones), self.col_count):
            checkbox: QCheckBox = self.cellWidget(row,i).findChild(QCheckBox)
            if checkbox.checkState() == Qt.CheckState.Checked:
                current_zones.append(i-11)
        return current_zones
    
    def sound_data_check(self) -> Optional[str]:
        if not self.current_flight.get('terminal'):
            return 'Терминал'
        if int(self.current_flight.get('direction_id')) == 1 and not self.current_flight.get('boarding_gates'):
            return 'Номер выхода'
        return False

    def update_schedule(self, is_delete: bool = None) -> None:
        self.current_flight = self.get_current_flight(self.get_current_row_id())
        url_file = QUrl(settings.api_url+'update_schedule')
        request = QtNetwork.QNetworkRequest(url_file)
        request.setHeader(QtNetwork.QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")
        self.API_post = QtNetwork.QNetworkAccessManager()
        body = QJsonDocument({
            'flight_id': self.current_flight.get('flight_id'),
            'audio_text_id': self.current_flight.get('audio_text_id'),
            'languages': self.get_current_languages(), 
            'zones': self.get_current_zones(),
            'is_deleted': is_delete
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

    def delete_schedule(self, delete_all_audio: bool = None) -> None:
        flight_id: int = self.current_flight.get('flight_id')
        audio_text_id: int = self.current_flight.get('audio_text_id')
        for row in reversed(range(self.model().rowCount())):
            indx = self.model().index(row, 0)
            if indx.data():
                row_flight_id, row_audio_text_id = map(int, indx.data().split('_'))
                if (row_flight_id == flight_id and delete_all_audio is True) or (row_flight_id == flight_id and row_audio_text_id == audio_text_id):
                    self.removeRow(row)
            else:
                break

    def on_checkbox_state_change(self) -> None:
        row, column = map(int, self.sender().objectName().split('_'))
        self.selectRow(row)
        self.update_schedule()
