import asyncio
import json

from PySide6.QtWidgets import QTableView, QHeaderView, QAbstractItemView, QComboBox
from PySide6.QtCore import Qt, Signal, QTimer, QUrl, QModelIndex
from PySide6 import QtNetwork
from qasync import asyncSlot

from UI.ComboboxDelegate import ComboboxDelegate
from UI.TableModel import TableModel
from globals import settings, logger, terminals, zones
from UI.SpeakerStatusBar import speaker_status_bar

class CustomTableView(QTableView):
    _table_type: int = None
    # table_type
    # 0 - Main
    # 1 - Background
    __API_manager__: list[QtNetwork.QNetworkAccessManager] = [
        QtNetwork.QNetworkAccessManager(),
        QtNetwork.QNetworkAccessManager()
    ]
    _timer: QTimer = QTimer()
    _play_signal: Signal = Signal(QtNetwork.QNetworkReply)
    _stop_signal: Signal = Signal(tuple)
    _error_signal: Signal = Signal(str)
    _autoplay_signal: Signal = Signal()
    _autoplay_files: dict = []
    _is_autoplay: bool = False
    _speaker_status_bar = speaker_status_bar

    _header = None
    _data = []
    _centered_columns = []
    _checkable_columns = None
    _combobox_columns = None
    _editable_columns = None

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
    
    async def get_table_data_from_API(self, url: str) -> None:
        self._timer.stop()
        url_file = QUrl(url)
        request = QtNetwork.QNetworkRequest(url_file)
        self.__API_manager__[self._table_type].get(request)
        self.__API_manager__[self._table_type].finished.connect(self._refresh_table)
    
    def _data_prepare(self, initial_data: list[dict]) -> list[tuple]:
        result = []
        match self._table_type:
            case 0:
                for data in initial_data:
                    if data.get('audio_text_description'):
                        audio_text = f"{data.get('audio_text')} ({data.get('audio_text_description')})"
                    else:
                        audio_text = f"{data.get('audio_text')}"
                    if data.get('event_time'):
                        audio_text += f" ({data.get('event_time')})"
                    result.append([
                        data.get('schedule_id'), 
                        (data.get('is_played'), data.get('job_time'), data.get('job_is_fact')), 
                        data.get('flight_number_full'), 
                        data.get('direction'), 
                        data.get('plan_flight_time'), 
                        data.get('public_flight_time'), 
                        audio_text, 
                        data.get('path'),
                        data.get('languages').get('RUS').get('display'), 
                        data.get('languages').get('TAT').get('display'),
                        data.get('languages').get('ENG').get('display'), 
                        data.get('terminal'), data.get('boarding_gates'),
                        *list(map(lambda i: True if i[0]+1 in data.get('zones_list') else False, enumerate(zones))),
                        (data.get('direction_id'), data.get('status_id'))
                    ])
            case 1:
                for data in initial_data:
                    result.append([str(data.get('audio_text_id')), data.get('name'),
                        data.get('languages').get('RUS').get('display'),
                        data.get('languages').get('TAT').get('display'),
                        data.get('languages').get('ENG').get('display'),
                        *list(map(lambda i: True if i[0]+1 in data.get('zones_list') else False, enumerate(zones)))
                    ])
        return result

    def _refresh_table(self, result: QtNetwork.QNetworkReply) -> None:
        match result.error():
            case QtNetwork.QNetworkReply.NetworkError.NoError:
                bytes_string = result.readAll()
                if data:= str(bytes_string, 'utf-8'):
                    self._data = self._data_prepare(json.loads(data))
                    model = TableModel(
                        parent=self,
                        header=self._header,
                        data=self._data,
                        centered_columns=self._centered_columns,
                        checkable_columns=self._checkable_columns,
                        editable_columns=self._editable_columns
                    )
                    self.setModel(model)
                    self.resizeRowsToContents()
                    self.model().dataChanged.connect(self._save_row_data)

                    # from PySide6.QtGui import QStandardItemModel, QStandardItem
                    # self._terminal_combobox_model = QStandardItemModel()
                    # for combo_indx in self._combobox_columns:
                    #     for i in range (0, self.model().rowCount(self)):
                    #         current_index = self.model().index(i, combo_indx)
                    #         current_data = current_index.data()
                    #         for indx, terminal in enumerate(terminals):
                    #             item = QStandardItem(terminal.get('name'))
                    #             item.setData(terminal)
                    #             self._terminal_combobox_model.setItem(indx, item)
                    #             if current_data == terminal.get('name'):
                    #                 curr_cmbbx_indx = self._terminal_combobox_model.rowCount()-1
                    #         terminal_combobox = QComboBox()
                    #         terminal_combobox.setModel(self._terminal_combobox_model)
                    #         terminal_combobox.setCurrentIndex(curr_cmbbx_indx)
                    #         terminal_combobox.setCursor(Qt.CursorShape.PointingHandCursor)
                    #         self.setIndexWidget(current_index, terminal_combobox)
                    self.selectionModel().selectionChanged.connect(self.set_current_row)
                    info_message = f"Данные объявлений получены[{self._table_type}]"
                    self._speaker_status_bar.setStatusBarText(text=info_message)

            case QtNetwork.QNetworkReply.NetworkError.ConnectionRefusedError:
                error_message = f"Ошибка подключения к API: {result.errorString()}"
                self._speaker_status_bar.setStatusBarText(text=error_message, is_error=True)

        self._timer.start()

    def get_current_terminal(self) -> None:
        return None

    def get_current_boarding_gates(self) -> None:
        return None
    
    @asyncSlot()
    async def _save_row_data(self, index: QModelIndex):
        self.selectRow(index.row())
        data = self._data[index.row()]
        # TODO 
        # save changes in db
    
    def set_current_row(self) -> str:
        self.current_row: str = self.model().index(self.currentIndex().row(), 0).data()

class ScheduleTable(CustomTableView):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        
        self._table_type = 0
        checkable_columns = [8,9,10,*[indx+13 for indx, _ in enumerate(zones)]]
        self._header = ('', 'Эфир', 'Рейс', '', 'План', 'Расч.', 'Текст объявления', 'Маршрут', 'РУС', 'ТАТ', 'АНГ', 'Терминал', 'Выход', *[str(zone.get('id')) for zone in zones], '')
        self._centered_columns = checkable_columns
        self._checkable_columns = checkable_columns
        self._editable_columns = [12]
        self._combobox_columns = [11]
        
        self.setModel(TableModel(self, self._header))

        self.setAlternatingRowColors(True)
        self.setMinimumWidth(500)
        self.verticalHeader().setHidden(True)
        
        self.setColumnHidden(0, True)
        self.setColumnHidden(len(self._header)-1, True)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        self.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)
        self.horizontalHeader().setSectionResizeMode(8, QHeaderView.ResizeMode.Fixed)
        self.horizontalHeader().setSectionResizeMode(9, QHeaderView.ResizeMode.Fixed)
        self.horizontalHeader().setSectionResizeMode(10, QHeaderView.ResizeMode.Fixed)
        self.horizontalHeader().setSectionResizeMode(11, QHeaderView.ResizeMode.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(12, QHeaderView.ResizeMode.ResizeToContents)
        self.setColumnWidth(1, 50)
        self.setColumnWidth(4, 50)
        self.setColumnWidth(5, 50)
        self.setColumnWidth(7, 240)
        self.setColumnWidth(8, 32)
        self.setColumnWidth(9, 32)
        self.setColumnWidth(10, 32)
        for i in range(0, len(zones)):
            self.horizontalHeader().setSectionResizeMode(13+i, QHeaderView.ResizeMode.Fixed)
            self.setColumnWidth(13+i, 32)
        self.horizontalHeader().setSectionResizeMode(13+len(zones), QHeaderView.ResizeMode.ResizeToContents)
        
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

        self.setItemDelegateForColumn(11, ComboboxDelegate(self))
        
        self._timer = QTimer()
        self._timer.setInterval(settings.schedule_update_time*1000)
        self._timer.timeout.connect(lambda: asyncio.ensure_future(self.get_table_data_from_API(settings.api_url+'get_scheduler')))

class BackgroundTable(CustomTableView):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        
        self._table_type = 1
        checkable_columns = [2,3,4,*[indx+5 for indx, _ in enumerate(zones)]]
        self._header = ('', 'Название', 'РУС', 'ТАТ', 'АНГ', *[str(zone.get('id')) for zone in zones])
        self._centered_columns = checkable_columns
        self._checkable_columns = checkable_columns
        
        self.setModel(TableModel(self, self._header))

        self.setAlternatingRowColors(True)
        self.setMaximumWidth(500)
        self.verticalHeader().setHidden(True)

        self.setColumnHidden(0, True)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.setColumnWidth(2, 32)
        self.setColumnWidth(3, 32)
        self.setColumnWidth(4, 32)
        for i in range(0, len(zones)):
            self.horizontalHeader().setSectionResizeMode(5+i, QHeaderView.ResizeMode.Fixed)
            self.setColumnWidth(5+i, 32)

        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

        self._timer = QTimer()
        self._timer.setInterval(settings.background_schedule_update_time*1000)
        self._timer.timeout.connect(lambda: asyncio.ensure_future(self.get_table_data_from_API(settings.api_url+'get_audio_background_text')))
