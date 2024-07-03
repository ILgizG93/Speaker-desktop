import json
import asyncio

from PySide6.QtWidgets import QTableWidget, QHeaderView, QAbstractItemView, QTableWidgetItem, QWidget, QCheckBox, QHBoxLayout
from PySide6.QtCore import Qt, QUrl, QTimer, QUrlQuery, QJsonDocument
from PySide6 import QtNetwork

from .Font import RobotoFont
from settings import SpeakerSetting


class TableCheckbox(QCheckBox):
    def __init__(self, row_indx, col_indx):
        super().__init__()        
        self.setObjectName(f'{row_indx}_{col_indx}')
        self.setStyleSheet("QCheckBox::indicator" "{" "width :20px;" "height : 20px;" "}")
        self.setFixedWidth(22)
        self.setFixedHeight(32)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

class ScheduleTable(QTableWidget):
    def __init__(self, header: tuple[str], zones: dict, settings: SpeakerSetting, parent=None) -> None:
        self.settings: SpeakerSetting = settings
        self.header: tuple[str] = header
        self.zones: dict = zones
        self.col_count: int = len(self.header)
        self.row_count: int = 0
        super().__init__(self.row_count, self.col_count, parent)

        self.font: RobotoFont = RobotoFont()
        self.current_schedule_id: int
        self.current_flight: dict = {}

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
        self.timer.setInterval(self.settings.schedule_update_time)
        self.timer.timeout.connect(lambda: asyncio.run(self.get_scheduler_data_from_API()))
    
    async def get_scheduler_data_from_API(self) -> None:
        self.timer.stop()
        url_file = QUrl(self.settings.api_url+'get_scheduler')
        request = QtNetwork.QNetworkRequest(url_file)
        self.API_manager = QtNetwork.QNetworkAccessManager()
        self.API_manager.get(request)
        self.API_manager.finished.connect(self.refresh_schedule_table)

    def refresh_schedule_table(self, result: QtNetwork.QNetworkReply) -> None:
        if result.error() == QtNetwork.QNetworkReply.NetworkError.NoError:
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
                    current_schedule: dict = list(filter(lambda d: data[0] == d.get('schedule_id'), self.schedule_data_origin))[0]
                    for col_indx, item in enumerate(data):
                        if col_indx in [2,3,4,10,11]:
                            element = QTableWidgetItem(item)
                            element.setFont(self.font.get_font())
                            element.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                            self.setItem(row_indx, col_indx, element)
                        elif col_indx in [i for i in range(11, 11+len(self.zones)+1)]:
                            widget = QWidget()
                            checkbox = TableCheckbox(row_indx, col_indx)
                            if current_schedule.get('flight_type_id') in self.zones[col_indx-12].get('flight_type'):
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

            print('Schedule data refreshed!')
            self.set_active_row()
            self.timer.start()

    def set_active_row(self) -> None:
        if self.current_flight.get('schedule_id'):
            for row in range(self.model().rowCount()):
                index = self.model().index(row, 0)
                if index.data() == self.current_flight.get('schedule_id'):
                    self.setCurrentIndex(index)
                    return
            self.selectRow(0)
        else:
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
    
    def update_schedule(self, is_delete: bool = None) -> None:
        url_file = QUrl(self.settings.api_url+'update_schedule')
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
    
    def delete_schedule(self):
        self.removeRow(self.currentRow())
        self.update_schedule(is_delete=True)

    def on_checkbox_state_change(self) -> None:
        row, column = map(int, self.sender().objectName().split('_'))
        self.selectRow(row)
        self.update_schedule()
