import json
import asyncio

from typing import Optional
from PySide6.QtWidgets import QTableWidget, QHeaderView, QAbstractItemView, QTableWidgetItem, QWidget, QCheckBox, QHBoxLayout, QTextEdit, QComboBox
from PySide6.QtCore import Qt, QUrl, QTimer, QUrl, QUrlQuery, QJsonDocument, Signal, QEvent
from PySide6.QtGui import QBrush, QColor, QStandardItem, QStandardItemModel, QFont
from PySide6 import QtNetwork

from globals import root_directory, settings, logger, TableCheckbox
from .Font import RobotoFont

class ComboBox(QComboBox):
    def wheelEvent(self, ev):
        if ev.type() == QEvent.Type.Wheel:
            ev.ignore()

class TextEdit(QTextEdit):
    enter_pressed_signal: Signal = Signal()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.enter_pressed_signal.emit()
            return
        super().keyPressEvent(event)

class ScheduleTable(QTableWidget):
    terminals: list[dict]
    current_schedule_id: str = None
    current_data: dict = {}
    current_sound_file: str = None
    play_signal: Signal = Signal(QtNetwork.QNetworkReply)
    stop_signal: Signal = Signal(tuple)
    error_signal: Signal = Signal(str)

    def __init__(self, header: tuple[str], zones: dict, parent=None) -> None:
        self.header: tuple[str] = header
        self.zones: dict = zones
        self.col_count: int = len(self.header)
        self.row_count: int = 0
        super().__init__(self.row_count, self.col_count, parent)

        self.font: RobotoFont = RobotoFont()

        self.setMinimumWidth(500)
        
        self.setHorizontalHeaderLabels(self.header)
        self.setColumnHidden(0, True)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        self.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)
        self.horizontalHeader().setSectionResizeMode(8, QHeaderView.ResizeMode.Fixed)
        self.horizontalHeader().setSectionResizeMode(9, QHeaderView.ResizeMode.Fixed)
        self.horizontalHeader().setSectionResizeMode(10, QHeaderView.ResizeMode.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(11, QHeaderView.ResizeMode.ResizeToContents)
        self.setColumnWidth(6, 220)
        self.setColumnWidth(7, 32)
        self.setColumnWidth(8, 32)
        self.setColumnWidth(9, 32)
        for i in range(0, len(self.zones)):
            self.horizontalHeader().setSectionResizeMode(12+i, QHeaderView.ResizeMode.Fixed)
            self.setColumnWidth(12+i, 32)
        self.horizontalHeader().setSectionResizeMode(12+len(self.zones), QHeaderView.ResizeMode.ResizeToContents)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    
        self.timer = QTimer()
        self.timer.setInterval(settings.schedule_update_time*1000)
        self.timer.timeout.connect(lambda: asyncio.run(self.get_scheduler_data_from_API()))

        from UI.SpeakerStatusBar import speaker_status_bar
        self.speaker_status_bar = speaker_status_bar
    
    async def get_scheduler_data_from_API(self, set_timer: bool = True, flight_id: int = None, audio_text_id: int = None, flight_number: str = None) -> None:
        self.timer.stop()
        url_file = QUrl(settings.api_url+'get_scheduler')
        query = QUrlQuery()
        if flight_id and audio_text_id:
            query.addQueryItem('flight_id', str(flight_id))
            query.addQueryItem('audio_text_id', str(audio_text_id))
        elif flight_number:
            query.addQueryItem('flight_number', flight_number)
        url_file.setQuery(query.query())

        request = QtNetwork.QNetworkRequest(url_file)
        self.API_manager = QtNetwork.QNetworkAccessManager()
        self.API_manager.get(request)
        self.API_manager.finished.connect(lambda reply: self.refresh_schedule_table(reply, set_timer, flight_id, audio_text_id))

    def refresh_schedule_table(self, result: QtNetwork.QNetworkReply, set_timer: bool, flight_id: int = None, audio_text_id: int = None) -> None:
        match result.error():
            case QtNetwork.QNetworkReply.NetworkError.NoError:
                self.schedule_data: list = []
                bytes_string = result.readAll()
                if len(str(bytes_string, 'utf-8')) == 0:
                    self.setRowCount(0)
                else:
                    if flight_id and audio_text_id:
                        received_data: dict = json.loads(str(bytes_string, 'utf-8'))[0]
                        is_has_row_in_table: bool = len(list(filter(lambda d: d.get('flight_id') == flight_id and d.get('audio_text_id') == audio_text_id, self.data_origin))) != 0                       
                        row_indx: int = 0
                        if is_has_row_in_table is not True:
                            self.data_origin.append(received_data)
                            self.data_origin = list(sorted(self.data_origin, key=lambda d: (d.get('datetime'), d.get('flight_id'), (d.get('queue') is None, d.get('queue') or 0) , d.get('schedule_id'))))
                            for indx, data in enumerate(self.data_origin):
                                if data.get('flight_id') == flight_id and data.get('audio_text_id') == audio_text_id:
                                    current_schedule: list = [data]
                                    row_indx = indx
                                    break
                        received_data: list[dict] = [self.data_origin[row_indx]]
                    else:
                        self.data_origin: list[dict] = json.loads(str(bytes_string, 'utf-8'))
                        received_data: list[dict] = self.data_origin
                    for data in received_data:
                        if data.get('audio_text_description'):
                            audio_text = f"{data.get('audio_text')} ({data.get('audio_text_description')})"
                        else:
                            audio_text = f"{data.get('audio_text')}"
                        self.schedule_data.append((
                            data.get('schedule_id'), data.get('flight_number_full'), data.get('direction'), data.get('plan_flight_time'), data.get('public_flight_time'), 
                            audio_text, data.get('airport'),
                            data.get('languages').get('RUS').get('display'),
                            data.get('languages').get('TAT').get('display'),
                            data.get('languages').get('ENG').get('display'), 
                            data.get('terminal'), data.get('boarding_gates'),
                            *list(map(lambda i: True if i[0]+1 in data.get('zones_list') else False, enumerate(self.zones))),
                            data.get('is_played'), data.get('direction_id')
                        ))
                    if flight_id and audio_text_id:
                        if is_has_row_in_table is not True:
                            self.insertRow(row_indx)
                            self.set_row_data(row_indx, self.schedule_data[0], received_data[0])
                            self.resizeRowToContents(row_indx)
                            self.selectRow(row_indx)
                    else:
                        if (len(self.schedule_data) == 0):
                            self.schedule_data = [(None,) * len(self.header)]
                            self.setRowCount(0)
                        else:
                            self.setRowCount(len(self.schedule_data))
                            for row_indx, data in enumerate(self.schedule_data):
                                current_schedule: list = list(filter(lambda d: data[0] == d.get('schedule_id'), self.data_origin))
                                if len(current_schedule) > 0:
                                    current_schedule: dict = current_schedule[0]
                                    self.set_row_data(row_indx, data, current_schedule)
                                else:
                                    self.removeRow(0)
                                self.resizeRowToContents(row_indx)
                info_message = "Данные обновлены"
                self.speaker_status_bar.setStatusBarText(text=info_message)
                self.set_active_row()

            case QtNetwork.QNetworkReply.NetworkError.ConnectionRefusedError:
                error_message = f"Данные не обновлены. Ошибка подключения к API: {result.errorString()}"
                self.speaker_status_bar.setStatusBarText(text=error_message, is_error=True)
        
        if set_timer:
            self.timer.start()

    def set_row_data(self, row_indx: int, data: dict, current_schedule: dict):
        for col_indx, item in enumerate(data):
            if col_indx in [2,3]:
                element = QTableWidgetItem(item)
                element.setFont(self.font.get_font())
                element.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.setItem(row_indx, col_indx, element)
            elif col_indx in [i for i in range(12, 11+len(self.zones)+1)]:
                widget = QWidget()
                checkbox = TableCheckbox(row_indx, col_indx)
                checkbox.setChecked(item)
                checkbox.checkStateChanged.connect(self.on_widget_state_change)
                layoutH = QHBoxLayout(widget)
                layoutH.addWidget(checkbox)
                layoutH.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.setCellWidget(row_indx, col_indx, widget)
            elif col_indx in [7,8,9]:
                widget = QWidget()
                layoutH = QHBoxLayout(widget)
                layoutH.setAlignment(Qt.AlignmentFlag.AlignCenter)
                if item:
                    checkbox = TableCheckbox(row_indx, col_indx)
                    checkbox.setChecked(col_indx-6 in current_schedule.get('languages_list'))
                    checkbox.checkStateChanged.connect(self.on_widget_state_change)
                    layoutH.addWidget(checkbox)
                self.setCellWidget(row_indx, col_indx, widget)
            elif col_indx in [10]:
                widget = QWidget()
                layoutH = QHBoxLayout(widget)
                layoutH.setAlignment(Qt.AlignmentFlag.AlignCenter)
                model = QStandardItemModel()
                combobox = ComboBox()
                combobox.setObjectName(f'{row_indx}_{col_indx}')
                combobox.setFont(self.font.get_font(10))
                combobox.setFixedSize(50, 26)
                combobox.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
                combobox.setCursor(Qt.CursorShape.PointingHandCursor)
                combobox.setModel(model)
                for terminal in self.terminals:
                    combobox_item = QStandardItem(terminal.get('name'))
                    combobox_item.setData(terminal)
                    model.appendRow(combobox_item)
                    if item == terminal.get('name'):
                        combobox.setCurrentIndex(model.rowCount()-1)
                combobox.currentIndexChanged[int].connect(self.on_widget_state_change)
                layoutH.addWidget(combobox)
                self.setCellWidget(row_indx, col_indx, widget)
            elif col_indx in [11]:
                widget = QWidget()
                if data[-1] == 1:
                    layoutH = QHBoxLayout(widget)
                    layoutH.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    text_edit = TextEdit(self)
                    text_edit.setObjectName(f'{row_indx}_{col_indx}')
                    text_edit.setText(item)
                    text_edit.setFont(self.font.get_font(10))
                    text_edit.setFixedSize(50, 30)
                    text_edit.enter_pressed_signal.connect(self.on_widget_state_change)
                    text_edit.selectionChanged.connect(self.select_current_row)
                    layoutH.addWidget(text_edit)
                self.setCellWidget(row_indx, col_indx, widget)
            elif col_indx in [11+len(self.zones)+1] and item:
                self.set_mark_in_cell(row_indx, col_indx)
            elif col_indx >= 18:
                ...
            else:
                element = QTableWidgetItem(item)
                element.setFont(self.font.get_font())
                if col_indx in [4]:
                    element.setForeground(QBrush(QColor(255, 25, 25)))
                if col_indx in [5] and data[-1] == 2:
                    element.setForeground(QBrush(QColor(50, 100, 255)))
                self.setItem(row_indx, col_indx, element)

    def set_mark_in_cell(self, row_indx: int, col_indx: int):
        element = QTableWidgetItem('✓')
        element.setFont(self.font.get_font(18))
        element.setForeground(QBrush(QColor(60, 150, 35)))
        element.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setItem(row_indx, col_indx, element)

    def get_current_row_id(self) -> str:
        try:
            row_id = self.item(self.currentRow(), 0).text()
        except AttributeError as err:
            return None
        return row_id
    
    def get_current_languages(self) -> list[int]:
        current_languages: list[int] = []
        row: int = self.currentRow()
        for i in range(7, 10):
            cell = self.cellWidget(row,i)
            if cell.findChild(QCheckBox) and cell.findChild(QCheckBox).checkState() == Qt.CheckState.Checked:
                current_languages.append(i-6)
        return current_languages
    
    def get_current_zones(self) -> list[int]:
        current_zones: list[int] = []
        row: int = self.currentRow()
        for i in range(self.col_count - len(self.zones)-1, self.col_count-1):
            checkbox: QCheckBox = self.cellWidget(row,i).findChild(QCheckBox)
            if checkbox.checkState() == Qt.CheckState.Checked:
                current_zones.append(i-11)
        return current_zones

    def get_current_terminal(self) -> str:
        row: int = self.currentRow()
        combobox: ComboBox = self.cellWidget(row,10).findChild(ComboBox)
        return combobox.currentText()

    def get_current_boarding_gates(self) -> Optional[list[int]]:
        row: int = self.currentRow()
        if self.cellWidget(row,11):
            if text_edit := self.cellWidget(row,11).findChild(TextEdit):
                if len(text_edit.toPlainText()) > 0:
                    return list(map(int, text_edit.toPlainText().split(',')))
    
    def get_current_row_data(self, row_id: str) -> dict:
        current_data = list(filter(lambda d: d.get('schedule_id') == row_id, self.data_origin))
        if current_data:
            return current_data[0]
        elif self.data_origin:
            return self.data_origin[0]
    
    def set_active_schedule_id(self) -> None:
        self.current_data = self.get_current_row_data(self.get_current_row_id())
        if self.current_data:
            self.current_schedule_id = self.current_data.get('schedule_id')

    def set_active_row(self) -> None:
        if self.current_data and self.current_data.get('schedule_id'):
            if self.current_schedule_id is None:
                self.set_active_schedule_id()
                self.selectRow(0)
            else:
                for row in range(self.model().rowCount()):
                    index = self.model().index(row, 0)
                    if index.data() == self.current_schedule_id:
                        self.setCurrentIndex(index)
                        return
        else:
            if self.data_origin:
                self.current_data = self.data_origin[0]
            self.selectRow(0)
    
    def sound_data_check(self) -> Optional[str]:
        if not self.current_data.get('terminal'):
            return 'Терминал'
        if int(self.current_data.get('direction_id')) == 1 and not self.current_data.get('boarding_gates'):
            return 'Номер выхода'
        return False

    async def get_audio_file(self):
        row_id = self.get_current_row_id()
        if row_id is None:
            self.current_sound_file = None
            error_message: str = f"Ошибка воспроизведения: Необходимо выбрать объявление"
            self.error_signal.emit(error_message)
            return
        
        self.current_data = self.get_current_row_data(row_id)
        self.current_sound_file = root_directory+'/'+settings.file_name
        self.current_schedule_id = self.current_data.get('schedule_id')

        check = self.sound_data_check()
        if check:
            error_message: str = f"Ошибка воспроизведения: Отсутствуют данные, необходимые для воспроизведения ({check})"
            self.error_signal.emit(error_message)
            return

        if len(self.get_current_languages()) == 0:
            error_message: str = "Ошибка воспроизведения: Необходимо выбрать хотя бы один язык для воспроизведения"
            self.error_signal.emit(error_message)
            return

        self.timer.stop()

        url_file = QUrl(settings.api_url+'get_scheduler_sound')
        query = QUrlQuery()
        query.addQueryItem('flight_id', str(self.current_data.get('flight_id')))
        query.addQueryItem('audio_text_id', str(self.current_data.get('audio_text_id')))
        url_file.setQuery(query.query())
        
        request = QtNetwork.QNetworkRequest(url_file)
        self.API_manager = QtNetwork.QNetworkAccessManager()
        request.setHeader(QtNetwork.QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")
        body = QJsonDocument({
            'languages': self.get_current_languages(), 
            'zones': self.get_current_zones(),
            'terminal': self.get_current_terminal(),
            'boarding_gates': self.get_current_boarding_gates(),
        })
        
        reply = self.API_manager.post(request, body.toJson())
        self.API_manager.finished.connect(lambda: self.play_signal.emit(reply))

    def update_schedule(self, is_deleted: bool = None) -> None:
        self.current_data = self.get_current_row_data(self.get_current_row_id())
        url_file = QUrl(settings.api_url+'update_schedule')
        request = QtNetwork.QNetworkRequest(url_file)
        request.setHeader(QtNetwork.QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")
        self.API_post = QtNetwork.QNetworkAccessManager()
        body = QJsonDocument({
            'id': self.current_data.get('id'),
            'flight_id': self.current_data.get('flight_id'),
            'audio_text_id': self.current_data.get('audio_text_id'),
            'languages': self.get_current_languages(), 
            'zones': self.get_current_zones(),
            'terminal': self.get_current_terminal(),
            'boarding_gates': self.get_current_boarding_gates(),
            'is_deleted': is_deleted
        })
        self.API_post.post(request, body.toJson())
        self.API_post.finished.connect(self.after_update_schedule)

    def set_schedule_is_played(self) -> None:
        self.current_data = self.get_current_row_data(self.get_current_row_id())
        url_file = QUrl(settings.api_url+'set_schedule_is_played')
        request = QtNetwork.QNetworkRequest(url_file)
        request.setHeader(QtNetwork.QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")
        self.API_post = QtNetwork.QNetworkAccessManager()
        body = QJsonDocument({
            'flight_id': self.current_data.get('flight_id'),
            'audio_text_id': self.current_data.get('audio_text_id')
        })
        self.API_post.post(request, body.toJson())
        self.API_post.finished.connect(self.after_update_schedule)

    def after_update_schedule(self, result: QtNetwork.QNetworkReply) -> None:
        match result.error():
            case QtNetwork.QNetworkReply.NetworkError.NoError:
                self.current_data['terminal'] = self.get_current_terminal()
                self.current_data['boarding_gates'] = self.get_current_boarding_gates()
                logger.info(f"Данные сохранены")

            case QtNetwork.QNetworkReply.NetworkError.ConnectionRefusedError:
                error_message = f"Данные не сохранены. Ошибка подключения к API: {result.errorString()}"
                self.speaker_status_bar.setStatusBarText(text=error_message, is_error=True)

    def delete_schedule(self, delete_all_audio: bool = None) -> None:
        flight_id: int = self.current_data.get('flight_id')
        audio_text_id: int = self.current_data.get('audio_text_id')
        current_row_number = self.currentRow()
        for row in reversed(range(self.model().rowCount())):
            indx = self.model().index(row, 0)
            if indx.data():
                row_flight_id, row_audio_text_id = map(int, indx.data().split('_'))
                if (row_flight_id == flight_id and delete_all_audio is True) or (row_flight_id == flight_id and row_audio_text_id == audio_text_id):
                    self.data_origin.pop(row)
                    self.removeRow(row)
                self.selectRow(current_row_number)
            else:
                break
        
    def select_current_row(self) -> None:
        row, column = map(int, self.sender().objectName().split('_'))
        self.selectRow(row)

    def on_widget_state_change(self) -> None:
        row, column = map(int, self.sender().objectName().split('_'))
        self.selectRow(row)
        self.update_schedule()
