import asyncio
import requests
import os

import sounddevice as sd
import soundfile as sf
from math import ceil
from functools import partial
from typing import Optional

from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt, QTimer, QUrl, QUrlQuery, QSaveFile, QIODevice, QJsonDocument
from PySide6.QtGui import QIcon
from PySide6 import QtNetwork

from globals import root_directory, settings, interface, logger, exit_program_bcs_err
from .Font import RobotoFont
from .ScheduleTable import ScheduleTable
from .PlayerButtonLayout import PlayerButtonLayout
from .BackgroundTable import BackgroundTable
from .AudioTextDialog import AudioTextDialog
from .DeleteAudioTextDialog import DeleteAudioTextDialog
from .DeleteBackgroundDialog import DeleteBackgroundDialog
from .MessageDialog import MessageDialog

class SpeakerException(Exception):
    def __init__(self, message, extra_info):
        super().__init__(message)
        self.extra_info = extra_info


class SpeakerApplication(QMainWindow):
    def __init__(self):
        super().__init__()
        self.user_uuid = 'e8c1c5d1-dfa5-4252-ad97-5d3d222794e1'

        font = RobotoFont()

        logger.info(f'Начало загрузки формы приложения')

        try:
            zones_request = requests.get(settings.api_url+'get_zones')
        except requests.exceptions.ConnectionError as err:
            error_message: str = "Ошибка подключения к API:\n{1!r}".format(type(err).__name__, err.args)
            logger.error(error_message)
            self.open_message_dialog(error_message)
            exit_program_bcs_err()
        else:
            self.zones: list[dict] = zones_request.json()


        self.play_finish_timer = QTimer()
        self.device_id = interface.system_device.get(settings.device.get('name'))
        if self.device_id is None:
            error_message = "Аудио устройство не обнаружено"
            logger.error(error_message)
            self.open_message_dialog(error_message)
            exit_program_bcs_err()

        self.samplerate = settings.device.get('samplerate')

        self.setWindowTitle("Speaker 2.0")
        self.setWindowIcon(QIcon("../resources/icons/app/icon.png"))
        self.setGeometry(100, 100, 1280, 720)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.layout: QHBoxLayout = QHBoxLayout(self.central_widget)

        # menu = self.menuBar()
        # menu.setFont(font.get_font(10))

        # setting_action = QAction("&Настройки", self)
        # setting_action.triggered.connect(lambda: print('Настройки'))
        # setting_action.setFont(font.get_font(10))
        # menu.addAction(setting_action)
        # setting_action = QAction("&Зоны", self)
        # setting_action.triggered.connect(lambda: print('Зоны'))
        # setting_action.setFont(font.get_font(10))
        # menu.addAction(setting_action)
        # setting_action = QAction("&Объявления", self)
        # setting_action.triggered.connect(lambda: print('Объявления'))
        # setting_action.setFont(font.get_font(10))
        # menu.addAction(setting_action)
        # setting_action = QAction("&Фоновые объявления", self)
        # setting_action.triggered.connect(lambda: print('Фоновые объявления'))
        # setting_action.setFont(font.get_font(10))
        # menu.addAction(setting_action)

        self.schedule_header = ('', 'Номер рейса', '', 'Время (План)', 'Время (Расч.)', 'Текст объявления', 'Маршрут', 'РУС', 'ТАТ', 'АНГ', 'Терминал', 'Выход', *[str(zone.get('id')) for zone in self.zones], 'Озвучено')
        self.schedule_data = [(None,) * len(self.schedule_header)]

        self.schedule_layout = QVBoxLayout()
        
        self.schedule_label = QLabel()
        self.schedule_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.schedule_label.setText('Объявления')

        self.schedule_table = ScheduleTable(self.schedule_header, self.zones)
        self.schedule_table.selectionModel().selectionChanged.connect(self.schedule_table.set_active_schedule_id)

        self.schedule_button_layout = PlayerButtonLayout()
        self.schedule_button_layout.btn_sound_create.clicked.connect(self.open_audio_text_dialog)
        self.schedule_button_layout.btn_sound_play.clicked.connect(lambda: asyncio.run(self.start_playing(self.schedule_table, self.schedule_button_layout)))
        self.schedule_button_layout.btn_sound_stop.clicked.connect(lambda: self.stop_play(self.schedule_table, self.schedule_button_layout, True))
        self.schedule_button_layout.btn_sound_delete.clicked.connect(partial(self.open_delete_audio_text_dialog, self.schedule_table))

        self.schedule_manipulation_layout = QHBoxLayout()
        self.schedule_manipulation_layout.addLayout(self.schedule_button_layout)
        
        self.schedule_layout.addWidget(self.schedule_label)
        self.schedule_layout.addWidget(self.schedule_table)
        self.schedule_layout.addLayout(self.schedule_manipulation_layout)
        
        self.background_header = ('', 'Название', 'РУС', 'ТАТ', 'АНГ', *[str(zone.get('id')) for zone in self.zones])
        self.background_data = [(None,) * len(self.schedule_header)]

        self.background_layout = QVBoxLayout()
        
        self.background_label = QLabel()
        self.background_label.setMaximumWidth(340)
        self.background_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.background_label.setText('Фоновые объявления')
        
        self.background_table = BackgroundTable(self.background_header, self.zones)
        self.background_table.selectionModel().selectionChanged.connect(self.background_table.set_active_schedule_id)

        self.background_button_layout = PlayerButtonLayout()
        # self.background_button_layout.btn_sound_create.clicked.connect(self.open_audio_text_dialog)
        self.background_button_layout.btn_sound_create.setHidden(True)
        self.background_button_layout.btn_sound_play.clicked.connect(lambda: asyncio.run(self.start_playing(self.background_table, self.background_button_layout)))
        self.background_button_layout.btn_sound_stop.clicked.connect(lambda: self.stop_play(self.background_table, self.background_button_layout, True))
        self.background_button_layout.btn_sound_delete.clicked.connect(partial(self.open_delete_audio_text_dialog, self.background_table))

        self.background_manipulation_layout = QHBoxLayout()
        self.background_manipulation_layout.addLayout(self.background_button_layout)

        self.background_layout.addWidget(self.background_label)
        self.background_layout.addWidget(self.background_table)
        self.background_layout.addLayout(self.background_manipulation_layout)

        self.layout.addLayout(self.schedule_layout)
        self.layout.addLayout(self.background_layout)

        self.schedule_label.setFont(font.get_font(18))
        self.background_label.setFont(font.get_font(18))
        
        self.schedule_table.play_signal.connect(lambda data, table = self.schedule_table, buttons = self.schedule_button_layout: self.save_sound_file(table, buttons, data))
        self.schedule_table.stop_signal.connect(self.get_stop_signal)
        self.schedule_table.error_signal.connect(lambda data, table = self.schedule_table, buttons = self.schedule_button_layout: self.get_error(table, buttons, data))
        self.background_table.play_signal.connect(lambda data, table = self.background_table, buttons = self.background_button_layout: self.save_sound_file(table, buttons, data))
        self.background_table.stop_signal.connect(self.get_stop_signal)
        self.background_table.error_signal.connect(lambda data, table = self.background_table, buttons = self.background_button_layout: self.get_error(table, buttons, data))

        from .SpeakerStatusBar import speaker_status_bar
        self.setStatusBar(speaker_status_bar)
        self.statusBar().setStyleSheet("font-size: 16px")

    def set_play_buttons_disabled(self, disabled: bool = False):
        if disabled:
            self.schedule_button_layout.btn_sound_play.setDisabled(True)
            self.background_button_layout.btn_sound_play.setDisabled(True)
        else:
            self.schedule_button_layout.btn_sound_play.setEnabled(True)
            self.background_button_layout.btn_sound_play.setEnabled(True)

    async def start_playing(self, table: ScheduleTable | BackgroundTable, buttons: PlayerButtonLayout):
        self.set_play_buttons_disabled(True)
        buttons.btn_sound_play.setHidden(True)
        buttons.btn_sound_stop.setVisible(True)
        buttons.btn_sound_stop.setDisabled(True)
        await table.get_audio_file()
    
    def get_error(self, table: ScheduleTable | BackgroundTable, buttons: PlayerButtonLayout, error_message: str) -> None:
        table.speaker_status_bar.setStatusBarText(text=error_message, is_error=True)
        self.open_message_dialog(error_message)
        self.stop_play(table, buttons)

    def get_stop_signal(self, reply):
        print('stop play', reply)

    def save_sound_file(self, table: ScheduleTable | BackgroundTable, buttons: PlayerButtonLayout, data: QtNetwork.QNetworkReply):
        buttons.btn_sound_stop.setEnabled(True)
        self.file = QSaveFile(table.current_sound_file)
        data = data.readAll()
        if len(data) == 0:
            self.get_error("Ошибка воспроизведения: Файл не сформирован.")
            return
        self.file.open(QIODevice.OpenModeFlag.WriteOnly)
        self.file.write(data)
        self.file.commit()
        self.play_sound(table, buttons)

    def save_action_history(self, user_uuid: str, table: ScheduleTable | BackgroundTable, action: str) -> None:
        url_file = QUrl(settings.api_url+'save_action_history')
        query = QUrlQuery()
        url_file.setQuery(query.query())
        body = QJsonDocument({
            'user_id': user_uuid,
            'flight_id': table.current_data.get('flight_id'),
            'audio_text_id': table.current_data.get('audio_text_id'),
            'languages': ','.join(map(str, table.get_current_languages())),
            'zones': ','.join(map(str, table.get_current_zones())),
            'action': action
        })
        request = QtNetwork.QNetworkRequest(url_file)
        request.setHeader(QtNetwork.QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")
        self.API_history = QtNetwork.QNetworkAccessManager()
        self.API_history.post(request, body.toJson())

    def play_sound(self, table: ScheduleTable | BackgroundTable, buttons: PlayerButtonLayout) -> None:
        table.setDisabled(True)
        buttons.btn_sound_delete.setDisabled(True)

        file = sf.SoundFile(table.current_sound_file)
        duration = ceil(file.frames / file.samplerate) * 1_000
        
        data, _ = sf.read(table.current_sound_file)
        sd.default.device = self.device_id
        sd.default.samplerate = self.samplerate
        if len(table.get_current_zones()) == 0:
            self.get_error("Ошибка воспроизведения: Необходимо выбрать хотя бы одну зону для воспроизведения")
            return
        try:
            sd.play(data, mapping=table.get_current_zones())
        except sd.PortAudioError as err:
            self.get_error("Ошибка воспроизведения: Аудио устройство не подключено")
            return

        self.save_action_history(user_uuid=self.user_uuid, table=table, action='Воспроизведение объявления')

        self.play_finish_timer.setInterval(duration)
        self.play_finish_timer.timeout.connect(lambda: self.stop_play(table, buttons))
        self.play_finish_timer.start()

    def stop_play(self, table: ScheduleTable | BackgroundTable, buttons: PlayerButtonLayout, is_manual_pressed: bool = False) -> None:
        if os.path.isfile(table.current_sound_file):
            os.unlink(table.current_sound_file)
        self.set_play_buttons_disabled(False)
        table.setEnabled(True)
        buttons.btn_sound_delete.setEnabled(True)
        sd.stop()
        table.timer.start()
        self.play_finish_timer.stop()
        buttons.btn_sound_play.setVisible(True)
        buttons.btn_sound_stop.setHidden(True)
        if is_manual_pressed:
            self.save_action_history(user_uuid=self.user_uuid, table=table, action='Ручная остановка воспроизведения')
        elif table.__class__.__name__ == 'ScheduleTable':
            table.set_mark_in_cell(table.currentRow(), table.col_count-1)
            table.set_schedule_is_played()

    def open_audio_text_dialog(self) -> None:
        self.schedule_table.timer.stop()
        flight_id, _ = map(int, self.schedule_table.get_current_row_id().split('_'))
        self.audio_text_dialog = AudioTextDialog(self)
        self.audio_text_dialog.flight_combobox_model.clear()
        asyncio.run(self.audio_text_dialog.get_flights_from_API(flight_id))
        asyncio.run(self.audio_text_dialog.get_audio_text_from_API())
        asyncio.run(self.audio_text_dialog.get_audio_text_reasons_from_API())
        asyncio.run(self.audio_text_dialog.get_terminal_from_API())
        self.audio_text_dialog.audio_text_info_layout.itemAt(0).widget().setText('')
        self.audio_text_dialog.append_signal.connect(self.schedule_table_after_append)
        self.audio_text_dialog.exec()

    def schedule_table_after_append(self, reply: tuple = None):
        if reply:
            reply_code, reply_message, reply_body = reply
            if reply_code in [200]:
                self.schedule_table.current_schedule_id = f"{reply_body.get('flight_id')}_{reply_body.get('audio_text_id')}"
                asyncio.run(self.schedule_table.get_scheduler_data_from_API(reply_body.get('flight_id'), reply_body.get('audio_text_id')))
            self.open_message_dialog(reply_message)
        self.schedule_table.timer.start()

    def open_delete_audio_text_dialog(self, table: ScheduleTable | BackgroundTable) -> None:
        match table.__class__.__name__:
            case 'ScheduleTable':
                self.delete_audio_text_dialog: DeleteAudioTextDialog = DeleteAudioTextDialog(self)
                self.delete_audio_text_dialog.delete_flight_checkbox.setChecked(False)
            case 'BackgroundTable':
                self.delete_audio_text_dialog: DeleteBackgroundDialog = DeleteBackgroundDialog(self)

        row_id = table.get_current_row_id()
        if row_id is None:
            error_message: str = "Ошибка удаления: Необходимо выбрать объявление"
            logger.error(error_message)
            self.open_message_dialog(error_message)
            return
        table.timer.stop()
        table.current_data = table.get_current_row_data(row_id)
        self.delete_audio_text_dialog.data = table.data_origin
        self.delete_audio_text_dialog.set_message_text(table.current_data)
        self.delete_audio_text_dialog.set_data(table.current_data)
        self.delete_audio_text_dialog.delete_signal.connect(lambda data: self.after_delete_audio_from_table(table, data))
        self.delete_audio_text_dialog.exec()
        self.delete_audio_text_dialog.btn_message_close.setFocus()

    def after_delete_audio_from_table(self, table: ScheduleTable | BackgroundTable, result: Optional[QtNetwork.QNetworkReply] = None) -> None:
        if result:
            match result.error():
                case QtNetwork.QNetworkReply.NetworkError.NoError:
                    info_message = "Объявление удалено"
                    logger.info(info_message)
                    if table.__class__.__name__ == 'ScheduleTable':
                        delete_all_audio: bool = self.delete_audio_text_dialog.delete_all_audio
                        table.delete_schedule(delete_all_audio)
                    else:
                        table.delete_schedule()
                    self.open_message_dialog(info_message)

                case QtNetwork.QNetworkReply.NetworkError.ConnectionRefusedError:
                    error_message = f"Объявление не удалено. Ошибка подключения к API: {result.errorString()}"
                    logger.error(error_message)
                    self.open_message_dialog(error_message)

        table.timer.start()
        self.delete_audio_text_dialog.destroy()

    def open_message_dialog(self, message: str) -> None:
        self.message_dialog: MessageDialog = MessageDialog(self, message)
        self.message_dialog.exec()
