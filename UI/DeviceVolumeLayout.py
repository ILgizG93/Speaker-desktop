from PySide6.QtWidgets import QVBoxLayout, QLabel, QSlider, QFrame
from PySide6.QtCore import Qt

class DeviceVolumeLayout(QVBoxLayout):
    def __init__(self, interface, device):
        super().__init__()
        self.interface = interface
        self.device_id = device.get('device_ID')

        self.zone_label = QLabel(device.get('location'))
        self.zone_label.setAlignment(Qt.AlignHCenter)
        self.zone_label.setMinimumWidth(140)
        self.zone_label.setMaximumWidth(180)
        self.zone_label.setMaximumHeight(24)
        self.zone_label.setFrameStyle(QFrame.Panel | QFrame.Raised)
        self.zone_label.setLineWidth(3)
        self.addWidget(self.zone_label)

        self.device_label = QLabel(device.get('name', ''))
        self.device_label.setAlignment(Qt.AlignHCenter)
        self.device_label.setMaximumWidth(180)
        self.device_label.setMaximumHeight(24)
        self.addWidget(self.device_label)

        self.current_volume = device.get('volume')
        self.volume_slider = QSlider(Qt.Vertical)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(int(self.current_volume))
        self.volume_slider.setMaximumWidth(180)
        self.volume_slider.setMinimumHeight(100)
        self.volume_slider.setMaximumHeight(200)
        self.volume_slider.valueChanged.connect(self.set_volume)
        self.addWidget(self.volume_slider, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.volume_value_label = QLabel(f"{self.current_volume}%")
        self.volume_value_label.setAlignment(Qt.AlignHCenter)
        self.volume_value_label.setMaximumWidth(180)
        self.volume_value_label.setMaximumHeight(20)
        self.addWidget(self.volume_value_label)

    def set_volume(self, volume):
        self.interface.set_device_volume(self.device_id, int(volume))
        self.volume_value_label.setText(f"{int(volume)}%")
        self.current_volume = volume
