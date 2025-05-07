from PySide6.QtWidgets import QGridLayout, QLabel, QDialog, QCheckBox
from PySide6.QtCore import Qt, QUrl, QUrlQuery, QJsonDocument, Signal
from PySide6.QtGui import QIcon
from PySide6 import QtNetwork

from globals import settings
from .Font import RobotoFont
from .SpeakerButton import SpeakerButton

class DeleteAudioTextDialog(QDialog):
    data: list[dict] = None
    delete_all_audio: bool = None
    delete_signal: Signal = Signal(QtNetwork.QNetworkReply)
    
    def __init__(self, parent) -> None:
        super().__init__(parent)

        self.setWindowTitle("Удаление объявлений")
        self.setWindowIcon(QIcon("icons/app/icon.png"))
        self.setFixedSize(450, 200)
        font = RobotoFont()

        self.layout: QGridLayout = QGridLayout(self)

        self.message_label: QLabel = QLabel()
        self.message_label.setFont(font.get_font())
        self.message_label.setWordWrap(True)
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignJustify)

        self.delete_flight_checkbox: QCheckBox = QCheckBox("Удалить ВСЕ объявления этого рейса")
        self.delete_flight_checkbox.setObjectName("flight_checkbox")
        self.delete_flight_checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
        self.delete_flight_checkbox.setStyleSheet("margin: 10px 0px; font-size: 14px; color:red;")
        self.delete_flight_checkbox.setMaximumWidth(265)

        self.btn_message_delete: SpeakerButton = SpeakerButton(text='Удалить')
        self.btn_message_delete.clicked.connect(self.delete_audio_text)
        self.btn_message_close: SpeakerButton = SpeakerButton(text='Закрыть')
        self.btn_message_close.clicked.connect(self.close)

        self.layout.addWidget(self.message_label, 0, 0, 1, 2, alignment=Qt.AlignmentFlag.AlignTop)
        self.layout.addWidget(self.delete_flight_checkbox, 1, 0, 1, 2)
        self.layout.addWidget(self.btn_message_delete, 2, 0, alignment=Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.btn_message_close, 2, 1, alignment=Qt.AlignmentFlag.AlignCenter)

    def set_data(self, flight: dict) -> None:
        self.flight: dict = flight

    def set_message_text(self, flight: dict) -> None:
        self.message_label.setText(f"""Рейс {flight.get('flight_number_full')}.\n\nУдалить объявление "{flight.get('audio_text')}" из расписания?""")

    def delete_audio_text(self) -> None:
        self.delete_all_audio: bool = self.delete_flight_checkbox.checkState() == Qt.CheckState.Checked
        self.delete_audio_from_schedule()

    def delete_audio_from_schedule(self) -> None:
        flight_id: int = self.flight.get('flight_id')
        if self.delete_all_audio:
            flight_list: list = list(filter(lambda d: flight_id == d.get('flight_id'), self.data))
            audio_text_id_list: list = [f.get('audio_text_id') for f in flight_list]
        else:
            audio_text_id_list: list = [self.flight.get('audio_text_id')]
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
        self.API_post.finished.connect(self.delete_signal.emit)
    
    def closeEvent(self, event) -> None:
        self.delete_signal.emit(None)
