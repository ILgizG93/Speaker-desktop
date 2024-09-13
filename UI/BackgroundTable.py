import json
import asyncio

from PySide6.QtWidgets import QTableWidget, QHeaderView, QAbstractItemView, QWidget, QHBoxLayout, QTableWidgetItem, QStatusBar
from PySide6.QtCore import Qt, QUrl, QTimer
from PySide6 import QtNetwork

from globals import settings, TableCheckbox
from .Font import RobotoFont

class BackgroundTable(QTableWidget):
    def __init__(self, header, zones: dict, parent=None):
        self.header: tuple[str] = header
        self.zones: dict = zones
        self.col_count: int = len(self.header)
        self.row_count: int = 0
        super().__init__(self.row_count, self.col_count, parent)

        self.font: RobotoFont = RobotoFont()
        
        self.setMinimumWidth(540)
        self.setMaximumWidth(640)

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
        self.timer.setInterval(settings.background_schedule_update_time)
        self.timer.timeout.connect(lambda: asyncio.run(self.get_background_data_from_API()))

        from .SpeakerStatusBar import speaker_status_bar
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
                self.background_data_origin: list[dict] = json.loads(str(bytes_string, 'utf-8'))
                for data in self.background_data_origin:
                    self.background_data.append((data.get('desciption'), data.get('name'),
                        data.get('languages').get('RUS').get('display'),
                        data.get('languages').get('TAT').get('display'),
                        data.get('languages').get('ENG').get('display'),
                        *list(map(lambda i: True if i[0]+1 in data.get('zones_list') else False, enumerate(self.zones)))
                    ))
                if (len(self.background_data) == 0):
                    self.background_data = [(None,) * 2]
                else:
                    self.setRowCount(len(self.background_data))
                    for row_indx, data in enumerate(self.background_data):
                        current_schedule_background: list = list(filter(lambda d: data[0] == d.get('schedule_id'), self.background_data_origin))
                        if len(current_schedule_background) > 0:
                            current_schedule_background: dict = current_schedule_background[0]
                            for col_indx, item in enumerate(data):
                                if col_indx in []:
                                    element = QTableWidgetItem(item)
                                    element.setFont(self.font.get_font())
                                    element.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                                    self.setItem(row_indx, col_indx, element)
                                elif col_indx in [i for i in range(5, 5+len(self.zones)+1)]:
                                    widget = QWidget()
                                    checkbox = TableCheckbox(row_indx, col_indx)
                                    checkbox.setChecked(item)
                                    checkbox.checkStateChanged.connect(self.on_checkbox_state_change)
                                    layoutH = QHBoxLayout(widget)
                                    layoutH.addWidget(checkbox)
                                    layoutH.setAlignment(Qt.AlignmentFlag.AlignCenter)
                                    layoutH.setContentsMargins(0, 0, 0, 0)
                                    self.setCellWidget(row_indx, col_indx, widget)
                                elif col_indx in [2,3,4] and item:
                                    widget = QWidget()
                                    checkbox = TableCheckbox(row_indx, col_indx)
                                    checkbox.setChecked(col_indx-1 in current_schedule_background.get('languages_list'))
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
                info_message = "Фоновые объявления обновлены"
                self.speaker_status_bar.setStatusBarText(text=info_message)

            case QtNetwork.QNetworkReply.NetworkError.ConnectionRefusedError:
                error_message = f"Фоновые объявления. Ошибка подключения к API: {result.errorString()}"
                self.speaker_status_bar.setStatusBarText(text=error_message, is_error=True)

        self.timer.start()

    def on_checkbox_state_change(self) -> None:
        row, column = map(int, self.sender().objectName().split('_'))
        self.selectRow(row)
        # self.update_schedule()
