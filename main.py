import sys
import asyncio
import time

from PySide6.QtWidgets import QApplication, QProxyStyle
from PySide6.QtCore import QRect
from PySide6 import QtAsyncio

# from UI.Application import SpeakerApplication
from UI.MainWindow import SpeakerApplication
from globals import settings

class ProxyStyle(QProxyStyle):
    def subElementRect(self, element, opt, widget=None) -> QRect:
        if element == self.SubElement.SE_ItemViewItemCheckIndicator and not opt.text:
            rect = super().subElementRect(element, opt, widget)
            rect.moveCenter(opt.rect.center())
            return rect
        return super().subElementRect(element, opt, widget)

def main() -> None:
    app = QApplication(sys.argv)
    settings.apply_theme(settings.theme)
    # app.setStyle(ProxyStyle())

    speaker = SpeakerApplication()
    speaker.showMaximized()
    speaker.show()

    # asyncio.run(speaker.schedule_table.get_table_data_from_API(settings.api_url+'get_scheduler'))
    # asyncio.run(speaker.background_table.get_table_data_from_API(settings.api_url+'get_audio_background_text'))
    # QtAsyncio.run()

    asyncio.run(speaker.get_terminal_data_from_API())
    asyncio.run(speaker.background_table.get_background_data_from_API())
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
