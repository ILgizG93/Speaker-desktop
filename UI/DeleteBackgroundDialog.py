from PySide6.QtWidgets import QGridLayout, QLabel, QDialog
from PySide6.QtCore import Qt, QUrl, QUrlQuery, QJsonDocument, Signal
from PySide6.QtGui import QIcon
from PySide6 import QtNetwork

from globals import settings, logger
from .Font import RobotoFont
from .SpeakerButton import SpeakerButton

class DeleteBackgroundDialog(QDialog):
    delete_signal: Signal = Signal(QtNetwork.QNetworkReply)
    data: dict = None
    
    def __init__(self, parent):
        super().__init__(parent)

        self.setWindowTitle("Удаление фоновых объявлений")
        self.setWindowIcon(QIcon("icons/app/icon.png"))
        self.setFixedSize(450, 200)
        font = RobotoFont()

        self.layout: QGridLayout = QGridLayout(self)

        self.message_label: QLabel = QLabel()
        self.message_label.setFont(font.get_font())
        self.message_label.setWordWrap(True)
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignJustify)

        self.btn_message_delete: SpeakerButton = SpeakerButton(text='Удалить')
        self.btn_message_delete.clicked.connect(self.delete_audio_from_schedule)
        self.btn_message_close: SpeakerButton = SpeakerButton(text='Закрыть')
        self.btn_message_close.clicked.connect(self.close)

        self.layout.addWidget(self.message_label, 0, 0, 1, 2, alignment=Qt.AlignmentFlag.AlignTop)
        self.layout.addWidget(self.btn_message_delete, 2, 0, alignment=Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.btn_message_close, 2, 1, alignment=Qt.AlignmentFlag.AlignCenter)

    def set_data(self, audio: dict) -> None:
        self.audio: dict = audio

    def set_message_text(self, audio: dict) -> None:
        self.message_label.setText(f"""Удалить объявление "{audio.get('name')}" из фоновых объявлений?""")

    def delete_audio_from_schedule(self) -> None:
        audio_text_id: str = str(self.audio.get('audio_text_id'))
        self.btn_message_delete.setDisabled(True)
        url_file = QUrl(settings.api_url+'delete_audio_text')
        query = QUrlQuery()
        query.addQueryItem('audio_text_id', audio_text_id)
        url_file.setQuery(query.query())
        request = QtNetwork.QNetworkRequest(url_file)
        request.setHeader(QtNetwork.QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")
        self.API_post = QtNetwork.QNetworkAccessManager()
        self.API_post.post(request, QJsonDocument().toJson())
        self.API_post.finished.connect(self.delete_signal.emit)
    
    def closeEvent(self, event):
        self.delete_signal.emit(None)
