from PySide6.QtWidgets import QGridLayout, QLabel
from PySide6.QtCore import Qt

from .Font import RobotoFont

class ScheduleZoneLayout(QGridLayout):
    def __init__(self, zones: dict, parent=None) -> None:
        super().__init__(parent)
        self.zones = zones
        self.current_schedule_id = None
        self.setHorizontalSpacing(25)
        self.setContentsMargins(5, 10, 15, 10)
        self.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.add_zones_to_layout()
    
    def add_zones_to_layout(self) -> None:
        for zone in self.zones:
            zone_label = QLabel(f"{zone.get('id')}. {zone.get('name')}")
            zone_label.setFont(RobotoFont().get_font(14))
            zone_label.setWordWrap(True)
            self.addWidget(zone_label, (zone.get('id')-1) % 2, (zone.get('id')-1) // 2)
