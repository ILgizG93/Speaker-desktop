from PySide6.QtWidgets import QGridLayout, QLabel, QDialog, QCheckBox
from PySide6.QtCore import Qt, QUrl, QUrlQuery, QJsonDocument, Signal
from PySide6.QtGui import QIcon
from PySide6 import QtNetwork

from typing import Optional
from globals import settings, logger
from .Font import RobotoFont
from .SpeakerButton import SpeakerButton

class DeleteAudioTextDialog(QDialog):
    delete_all_audio: bool = None
    delete_signal: Signal = Signal(tuple)
    schedule_data: dict = None
    
    def __init__(self, parent):
        super().__init__(parent)

        self.setWindowTitle("Удаление объявлений")
        self.setWindowIcon(QIcon("icons/app/icon.png"))
        self.setFixedSize(450, 200)
        font = RobotoFont()

        self.layout: QGridLayout = QGridLayout(self)

        self.message_label = QLabel()
        self.message_label.setFont(font.get_font())
        self.message_label.setWordWrap(True)
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignJustify)

        self.delete_flight_checkbox = QCheckBox("Удалить ВСЕ объявления этого рейса")
        self.delete_flight_checkbox.setObjectName("flight_checkbox")
        self.delete_flight_checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
        self.delete_flight_checkbox.setStyleSheet("margin: 10px 0px; font-size: 14px; color:red;")
        self.delete_flight_checkbox.setMaximumWidth(265)

        self.btn_message_delete = SpeakerButton(text='Удалить')
        self.btn_message_delete.clicked.connect(self.delete_audio_text)
        self.btn_message_close = SpeakerButton(text='Закрыть')
        self.btn_message_close.clicked.connect(self.close)

        self.layout.addWidget(self.message_label, 0, 0, 1, 2, alignment=Qt.AlignmentFlag.AlignTop)
        self.layout.addWidget(self.delete_flight_checkbox, 1, 0, 1, 2)
        self.layout.addWidget(self.btn_message_delete, 2, 0, alignment=Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.btn_message_close, 2, 1, alignment=Qt.AlignmentFlag.AlignCenter)

    def set_flight(self, flight: dict) -> None:
        self.flight = flight

    def set_message_text(self, flight: dict) -> None:
        self.message_label.setText(f"""Рейс {flight.get('flight_number_full')}.\n\nУдалить объявление "{flight.get('audio_text')}" из расписания?""")

    def delete_audio_text(self):
        self.delete_all_audio = self.delete_flight_checkbox.checkState() == Qt.CheckState.Checked
        self.delete_audio_from_schedule()

    def delete_audio_from_schedule(self) -> None:
        flight_id = self.flight.get('flight_id')
        audio_text_id_list = []
        if self.delete_all_audio:
            flight_list: list = list(filter(lambda d: flight_id == d.get('flight_id'), self.schedule_data))
            audio_text_id_list = [f.get('audio_text_id') for f in flight_list]
        else:
            audio_text_id_list = [self.flight.get('audio_text_id')]
        audio_text_id_list = ','.join(map(str, audio_text_id_list))
        self.btn_message_delete.setDisabled(True)
        url_file = QUrl(settings.api_url+'delete_schedule')
        query = QUrlQuery()
        query.addQueryItem('flight_id', str(flight_id))
        query.addQueryItem('audio_text_id_list', audio_text_id_list)
        url_file.setQuery(query.query())
        request = QtNetwork.QNetworkRequest(url_file)
        request.setHeader(QtNetwork.QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")
        self.API_post = QtNetwork.QNetworkAccessManager()
        self.API_post.post(request, QJsonDocument().toJson())
        self.API_post.finished.connect(self.after_delete_audio_from_schedule)

    def after_delete_audio_from_schedule(self, result: QtNetwork.QNetworkReply) -> None:
        self.close()
        match result.error():
            case QtNetwork.QNetworkReply.NetworkError.NoError:
                info_message = "Объявление удалено"
                logger.info(info_message)
                reply = (200, info_message)

            case QtNetwork.QNetworkReply.NetworkError.ConnectionRefusedError:
                error_message = f"Объявление не удалено. Ошибка подключения к API: {result.errorString()}"
                logger.error(error_message)
                reply = (400, error_message)
        self.delete_signal.emit(reply)
    
    def closeEvent(self, event):
        self.delete_signal.emit(tuple())
