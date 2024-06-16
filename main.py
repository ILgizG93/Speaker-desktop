import sys
import asyncio

from PySide6.QtWidgets import QApplication

from settings import SpeakerSetting
from UI.MainWindow import SpeakerApplication
from WinAPI.Device import AudioInterface

def main():

    app = QApplication(sys.argv)
    settings = SpeakerSetting()
    interface = AudioInterface(settings)
    speaker = SpeakerApplication(settings, interface)
    # speaker.showMaximized()
    speaker.show()

    asyncio.run(speaker.get_fake_schedule_data())
    # asyncio.run(speaker.get_schedule_data_from_API())

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
