import sys
import asyncio

from PySide6.QtWidgets import QApplication

from settings import SpeakerSetting
from UI.MainWindow import SpeakerApplication
from WinAPI.Device import AudioInterface

def main():
    
    # sys.argv += ['-platform', 'windows:darkmode=2']
    app = QApplication(sys.argv)
    # app.setStyle("Fusion")
    settings = SpeakerSetting()

    interface = AudioInterface(settings)
    speaker = SpeakerApplication(settings, interface)
    # speaker.showMaximized()
    speaker.show()

    asyncio.run(speaker.schedule_table.get_scheduler_data_from_API())
    asyncio.run(speaker.get_background_data_from_API())

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
