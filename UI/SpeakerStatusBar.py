from datetime import datetime

from PySide6.QtWidgets import QStatusBar

from globals import logger

class SpeakerStatusBar(QStatusBar):
    def __init__(self) -> None:
        super().__init__()
        
    def setStatusBarText(self, text: str, is_error: bool = None) -> None:
        if is_error:
            timeout = 30000
            logger.error(text)
        else:
            timeout = 15000
            logger.info(text)
        self.showMessage(f"{datetime.now().strftime('%d.%m.%y %H:%M:%S')}: {text}", timeout)

speaker_status_bar = SpeakerStatusBar()
