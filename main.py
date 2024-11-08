import sys
import asyncio

from PySide6.QtWidgets import QApplication

from UI.MainWindow import SpeakerApplication
from globals import settings

def main():
    
    app = QApplication(sys.argv)
    settings.apply_theme(settings.theme)

    speaker = SpeakerApplication()
    speaker.showMaximized()
    speaker.show()

    asyncio.run(speaker.get_terminal_data_from_API())
    asyncio.run(speaker.background_table.get_background_data_from_API())

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
