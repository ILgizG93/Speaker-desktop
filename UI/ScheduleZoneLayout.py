import requests

from PySide6.QtWidgets import QCheckBox, QGridLayout
from PySide6.QtCore import Qt, QUrl, QUrlQuery, QJsonDocument
from PySide6 import QtNetwork

from .Font import RobotoFont

class ScheduleZone(QCheckBox):
    def __init__(self, zone, parent=None):
        super().__init__(parent)
        self.setFont(RobotoFont().get_font(14))
        self.setText(f"{zone.get('id')}. {zone.get('name')}")

class ScheduleZoneLayout(QGridLayout):
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.current_schedule_id = None
        self.setHorizontalSpacing(25)
        self.setContentsMargins(5, 10, 15, 10)
        self.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.add_zones_to_layout()
    
    def add_zones_to_layout(self):
        self.checkboxes = []

        req = requests.get(self.settings.api_url+'get_zones')
        zones = req.json()

        for zone in zones:
            checkbox = ScheduleZone(zone)
            checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
            self.addWidget(checkbox, (zone.get('id')-1) % 2, (zone.get('id')-1) // 2)
            self.checkboxes.append(checkbox)
    
    def set_zones(self, zones):
        zones = list(map(lambda item: item[1].setChecked(True) if item[0]+1 in zones else item[1].setChecked(False), enumerate(self.checkboxes)))
    
    def get_active_zones(self):
        active_zones = [self.itemAt(i).widget() for i in range(self.count())]
        return [indx+1 for indx, item in enumerate(active_zones) if item.checkState() == Qt.CheckState.Checked]

    def update_zones(self):
        if not self.current_schedule_id:
            return
        active_zones = self.get_active_zones()
        url_file = QUrl(self.settings.api_url+'update_zone')
        query = QUrlQuery()
        query.addQueryItem('schedule_id', self.current_schedule_id)
        url_file.setQuery(query.query())
        request = QtNetwork.QNetworkRequest(url_file)
        request.setHeader(QtNetwork.QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")
        self.API_zones = QtNetwork.QNetworkAccessManager()
        
        body = QJsonDocument({'zones': active_zones})
        self.API_zones.post(request, body.toJson())
