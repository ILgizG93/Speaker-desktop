import os
import sys

import logging
from settings import SpeakerSetting
from loggers import init_logger
from WinAPI.Device import AudioInterface

from PySide6.QtWidgets import QCheckBox
from PySide6.QtCore import Qt

root_directory = os.path.abspath(os.curdir)

settings: SpeakerSetting = SpeakerSetting()
interface: AudioInterface = AudioInterface(settings)
logger: logging = init_logger(settings.log_file_path, "speaker")

def exit_program_bcs_err():
    logger.info("Завершение работы программы из-за ошибки...")
    sys.exit(0)


class TableCheckbox(QCheckBox):
    def __init__(self, row_indx, col_indx):
        super().__init__()
        self.setObjectName(f'{row_indx}_{col_indx}')
        self.setStyleSheet("QCheckBox::indicator" "{" "width :20px;" "height : 20px;" "}")
        self.setFixedWidth(22)
        self.setFixedHeight(22)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
