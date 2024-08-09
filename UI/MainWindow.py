import json
import asyncio
import requests

import sounddevice as sd
import soundfile as sf
from math import ceil
from datetime import datetime, UTC
from typing import Optional

from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt, QTimer, QUrl, QUrlQuery, QSaveFile, QIODevice, QJsonDocument
from PySide6.QtGui import QIcon, QAction, QFont
from PySide6 import QtNetwork

from globals import root_directory, settings, interface, logger, exit_program_bcs_err
from .Font import RobotoFont
from .ScheduleTable import ScheduleTable
from .ScheduleButtonLayout import ScheduleButtonLayout
from .ScheduleZoneLayout import ScheduleZoneLayout
from .BackgroundTable import BackgroundTable
from .BackgroundButtonLayout import BackgroundButtonLayout
from .AudioTextDialog import AudioTextDialog
from .DeleteAudioTextDialog import DeleteAudioTextDialog
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
            self.zones = zones_request.json()


        self.play_finish_timer = QTimer()
        self.device_id = interface.system_device.get(settings.device.get('name'))
        if self.device_id is None:
            error_message = "Аудио устройство не обнаружено"
            logger.error(error_message)
            self.open_message_dialog(error_message)
            exit_program_bcs_err()

        self.samplerate = settings.device.get('samplerate')

        self.schedule_header = ('', 'Номер рейса', '', 'Время (План)', 'Время (Расч.)', 'Текст объявления', 'Маршрут', 'РУС', 'ТАТ', 'АНГ', 'Терминал', 'Выход', *[str(zone.get('id')) for zone in self.zones])
        self.schedule_data = [(None,) * len(self.schedule_header)]

        self.setWindowTitle("Speaker 2.0")
        self.setWindowIcon(QIcon("../resources/icons/app/icon.png"))
        self.setGeometry(100, 100, 1280, 720)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.layout: QHBoxLayout = QHBoxLayout(self.central_widget)

        menu = self.menuBar()
        menu.setFont(font.get_font(10))

        setting_action = QAction("&Настройки", self)
        setting_action.triggered.connect(lambda: print('Настройки'))
        setting_action.setFont(font.get_font(10))
        menu.addAction(setting_action)
        setting_action = QAction("&Зоны", self)
        setting_action.triggered.connect(lambda: print('Зоны'))
        setting_action.setFont(font.get_font(10))
        menu.addAction(setting_action)
        setting_action = QAction("&Объявления", self)
        setting_action.triggered.connect(lambda: print('Объявления'))
        setting_action.setFont(font.get_font(10))
        menu.addAction(setting_action)
        setting_action = QAction("&Фоновые объявления", self)
        setting_action.triggered.connect(lambda: print('Фоновые объявления'))
        setting_action.setFont(font.get_font(10))
        menu.addAction(setting_action)

        self.schedule_layout = QVBoxLayout()
        
        self.schedule_label = QLabel()
        self.schedule_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.schedule_label.setText('Объявления')

        self.schedule_table = ScheduleTable(self.schedule_header, self.zones)
        # self.schedule_table.selectionModel().selectionChanged.connect(self.get_current_sound)

        self.schedule_button_layout = ScheduleButtonLayout()
        self.schedule_button_layout.btn_sound_create.clicked.connect(self.open_audio_text_dialog)
        self.schedule_button_layout.btn_sound_play.clicked.connect(lambda: asyncio.run(self.get_sound_file()))
        self.schedule_button_layout.btn_sound_stop.clicked.connect(lambda: self.stop_play(True))
        # self.schedule_button_layout.btn_sound_delete.clicked.connect(self.schedule_table.delete_schedule)
        self.schedule_button_layout.btn_sound_delete.clicked.connect(self.open_delete_audio_text_dialog)
        # self.schedule_button_layout.btn_sound_play.setDisabled(True)
        # self.schedule_button_layout.btn_sound_delete.setDisabled(True)

        self.zone_layout = ScheduleZoneLayout(self.zones)

        self.mainpulation_layout = QHBoxLayout()
        self.mainpulation_layout.addLayout(self.schedule_button_layout)
        # self.mainpulation_layout.addLayout(self.zone_layout)
        
        self.schedule_layout.addWidget(self.schedule_label)
        self.schedule_layout.addWidget(self.schedule_table)
        self.schedule_layout.addLayout(self.mainpulation_layout)
        
        self.background_layout = QVBoxLayout()
        
        self.background_label = QLabel()
        self.background_label.setMaximumWidth(340)
        self.background_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.background_label.setText('Фоновые объявления')
        
        self.background_table = BackgroundTable()

        self.bg_button_layout = BackgroundButtonLayout()
        # TODO
        # self.bg_button_layout.btn_sound_create.clicked.connect()
        # self.bg_button_layout.btn_sound_play.clicked.connect(lambda: asyncio.run(self.get_sound_file()))
        # self.bg_button_layout.btn_sound_stop.clicked.connect(self.stop_play)
        # self.bg_button_layout.btn_sound_delete.clicked.connect(self.delete_sound)

        self.background_layout.addWidget(self.background_label)
        self.background_layout.addWidget(self.background_table)
        self.background_layout.addLayout(self.bg_button_layout)

        self.layout.addLayout(self.schedule_layout)
        self.layout.addLayout(self.background_layout)

        self.schedule_label.setFont(font.get_font(18))
        self.background_label.setFont(font.get_font(18))
        self.background_table.setFont(font.get_font())

        from .SpeakerStatusBar import speaker_status_bar
        self.setStatusBar(speaker_status_bar)
        # self.statusBar().setFont(QFont('Times', 25))
        self.statusBar().setStyleSheet("font-size: 16px")
    
    def get_error(self, error_message: str) -> None:
        self.schedule_table.speaker_status_bar.setStatusBarText(text=error_message, is_error=True)
        self.open_message_dialog(error_message)
        self.stop_play()

    async def get_sound_file(self):
        row_id = self.schedule_table.get_current_row_id()
        if row_id is None:
            self.get_error(f"Ошибка воспроизведения: Необходимо выбрать объявление")
            return
        
        self.schedule_table.current_flight = self.schedule_table.get_current_flight(row_id)

        if self.schedule_table:
            self.current_sound_file = root_directory+'/'+settings.file_url+self.schedule_table.current_flight.get('schedule_id')+settings.file_format
            self.schedule_table.current_schedule_id = self.schedule_table.current_flight.get('schedule_id')

        check = self.schedule_table.sound_data_check()
        if check:
            self.get_error(f"Ошибка воспроизведения: Отсутствуют данные, необходимые для воспроизведения ({check})")
            return

        if len(self.schedule_table.get_current_languages()) == 0:
            self.get_error("Ошибка воспроизведения: Необходимо выбрать хотя бы один язык для воспроизведения")
            return

        self.schedule_table.timer.stop()
        self.schedule_button_layout.btn_sound_play.setHidden(True)
        self.schedule_button_layout.btn_sound_stop.setVisible(True)

        url_file = QUrl(settings.api_url+'get_scheduler_sound')
        query = QUrlQuery()
        query.addQueryItem('schedule_id', self.schedule_table.current_flight.get('schedule_id'))
        url_file.setQuery(query.query())
        
        request = QtNetwork.QNetworkRequest(url_file)
        self.API_manager = QtNetwork.QNetworkAccessManager()
        request.setHeader(QtNetwork.QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")
        body = QJsonDocument({'languages': self.schedule_table.get_current_languages()})
        
        reply = self.API_manager.post(request, body.toJson())
        self.schedule_button_layout.btn_sound_stop.setDisabled(True)
        self.API_manager.finished.connect(lambda: asyncio.run(self.save_sound_file(reply)))
        
        # reply = self.API_manager.get(request)
        # self.API_manager.finished.connect(lambda: asyncio.run(self.save_sound_file(reply)))

    async def save_sound_file(self, data: QtNetwork.QNetworkReply):
        self.schedule_button_layout.btn_sound_stop.setEnabled(True)
        self.file = QSaveFile(self.current_sound_file)
        data = data.readAll()
        if len(data) == 0:
            self.get_error("Ошибка воспроизведения: Файл не сформирован.")
            return
        self.file.open(QIODevice.OpenModeFlag.WriteOnly)
        self.file.write(data)
        self.file.commit()
        self.play_sound()

    def save_action_history(self, user_uuid: str, action: str) -> None:
        url_file = QUrl(settings.api_url+'save_action_history')
        query = QUrlQuery()
        query.addQueryItem('user_uuid', user_uuid)
        query.addQueryItem('flight_id', str(self.schedule_table.current_flight.get('flight_id')))
        query.addQueryItem('audio_text_id', str(self.schedule_table.current_flight.get('audio_text_id')))
        query.addQueryItem('languages', ','.join(map(str, self.schedule_table.get_current_languages())))
        query.addQueryItem('zones', ','.join(map(str, self.schedule_table.get_current_zones())))
        query.addQueryItem('action_datetime', str(datetime.now(UTC).replace(tzinfo=None)))
        query.addQueryItem('action', action)
        url_file.setQuery(query.query())
        
        request = QtNetwork.QNetworkRequest(url_file)
        self.API_history = QtNetwork.QNetworkAccessManager()
        request.setHeader(QtNetwork.QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")
        body = QJsonDocument({'languages': 1})
        
        reply = self.API_history.post(request, body.toJson())

    def play_sound(self) -> None:
        self.schedule_table.setDisabled(True)
        self.schedule_button_layout.btn_sound_delete.setDisabled(True)

        file = sf.SoundFile(self.current_sound_file)
        duration = ceil(file.frames / file.samplerate) * 1_000
        
        data, _ = sf.read(self.current_sound_file)
        sd.default.device = self.device_id
        sd.default.samplerate = self.samplerate
        if len(self.schedule_table.get_current_zones()) == 0:
            self.get_error("Ошибка воспроизведения: Необходимо выбрать хотя бы одну зону для воспроизведения")
            return
        try:
            sd.play(data, mapping=self.schedule_table.get_current_zones())
        except sd.PortAudioError as err:
            self.get_error("Ошибка воспроизведения: Аудио устройство не подключено")
            return

        self.save_action_history(user_uuid=self.user_uuid, action='Воспроизведение объявления')

        self.play_finish_timer.setInterval(duration)
        self.play_finish_timer.timeout.connect(self.stop_play)
        self.play_finish_timer.start()

    def stop_play(self, is_manual_pressed: bool = False) -> None:
        self.schedule_table.setEnabled(True)
        self.schedule_button_layout.btn_sound_delete.setEnabled(True)
        sd.stop()
        self.schedule_table.timer.start()
        self.play_finish_timer.stop()
        self.schedule_button_layout.btn_sound_play.setVisible(True)
        self.schedule_button_layout.btn_sound_stop.setHidden(True)
        if is_manual_pressed:
            self.save_action_history(user_uuid=self.user_uuid, action='Ручная остановка воспроизведения')

    async def get_background_data_from_API(self) -> None:
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
                    self.background_data.append((data.get('desciption'), data.get('name')))
                if (len(self.background_data) == 0):
                    self.background_data = [(None,) * 2]
                self.background_table.table_model.setItems(self.background_data)
                info_message = "Фоновые объявления обновлены"
                self.schedule_table.speaker_status_bar.setStatusBarText(text=info_message)
       
            case QtNetwork.QNetworkReply.NetworkError.ConnectionRefusedError:
                error_message = f"Фоновые объявления. Ошибка подключения к API: {result.errorString()}"
                self.schedule_table.speaker_status_bar.setStatusBarText(text=error_message, is_error=True)

    def open_audio_text_dialog(self) -> None:
        self.schedule_table.timer.stop()
        flight_id, _ = map(int, self.schedule_table.get_current_row_id().split('_'))
        self.audio_text_dialog = AudioTextDialog(self)
        self.audio_text_dialog.flight_combobox_model.clear()
        asyncio.run(self.audio_text_dialog.get_flights_from_API(flight_id))
        asyncio.run(self.audio_text_dialog.get_audio_text_from_API())
        self.audio_text_dialog.audio_text_info_layout.itemAt(0).widget().setText('')
        self.audio_text_dialog.append_signal.connect(self.schedule_table_after_append)
        self.audio_text_dialog.exec()

    def schedule_table_after_append(self, reply: tuple = None):
        if reply:
            reply_code, reply_message, reply_body = reply
            if reply_code in (200, 409):
                self.schedule_table.current_schedule_id = '_'.join(map(str, reply_body.values()))
                asyncio.run(self.schedule_table.get_scheduler_data_from_API())
            self.open_message_dialog(reply_message)
        self.schedule_table.timer.start()

    def open_delete_audio_text_dialog(self) -> None:
        self.schedule_table.timer.stop()
        self.schedule_table.current_flight = self.schedule_table.get_current_flight(self.schedule_table.get_current_row_id())
        self.delete_audio_text_dialog = DeleteAudioTextDialog(self)
        self.delete_audio_text_dialog.delete_flight_checkbox.setChecked(False)
        self.delete_audio_text_dialog.set_message_text(self.schedule_table.current_flight)
        self.delete_audio_text_dialog.set_flight(self.schedule_table.current_flight)
        self.delete_audio_text_dialog.delete_signal.connect(self.schedule_table_after_delete)
        self.delete_audio_text_dialog.exec()
        self.delete_audio_text_dialog.btn_message_close.setFocus()

    def schedule_table_after_delete(self, reply: tuple = None):
        if reply:
            reply_code, reply_message = reply
            if reply_code == 200:
                delete_all_audio: bool = self.delete_audio_text_dialog.delete_all_audio
                self.schedule_table.delete_schedule(delete_all_audio)
            self.open_message_dialog(reply_message)
        self.schedule_table.timer.start()
        self.delete_audio_text_dialog.destroy()

    def open_message_dialog(self, message: str) -> None:
        self.message_dialog = MessageDialog(self, message)
        self.message_dialog.exec()
