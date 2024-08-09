from PySide6.QtWidgets import QVBoxLayout, QLabel, QSlider, QFrame
from PySide6.QtCore import Qt

from globals import interface

class DeviceVolumeLayout(QVBoxLayout):
    def __init__(self, device: dict):
        super().__init__()
        self.device_id = device.get('device_ID')

        self.zone_label = QLabel(device.get('location'))
        self.zone_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.zone_label.setMinimumWidth(140)
        self.zone_label.setMaximumWidth(180)
        self.zone_label.setMaximumHeight(24)
        self.zone_label.setFrameStyle(QFrame.Shape.Panel | QFrame.Shadow.Raised)
        self.zone_label.setLineWidth(3)
        self.addWidget(self.zone_label)

        self.current_volume = device.get('volume')
        self.volume_slider = QSlider(Qt.Orientation.Vertical)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(int(self.current_volume))
        self.volume_slider.setMaximumWidth(180)
        self.volume_slider.setMinimumHeight(100)
        self.volume_slider.setMaximumHeight(200)
        self.volume_slider.valueChanged.connect(self.set_volume)
        self.addWidget(self.volume_slider, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.volume_value_label = QLabel(f"{self.current_volume}%")
        self.volume_value_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.volume_value_label.setMaximumWidth(180)
        self.volume_value_label.setMaximumHeight(20)
        self.addWidget(self.volume_value_label)

    def set_volume(self, volume):
        interface.set_device_volume(self.device_id, int(volume))
        self.volume_value_label.setText(f"{int(volume)}%")
        self.current_volume = volume
