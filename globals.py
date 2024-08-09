import os
import sys

import logging
from settings import SpeakerSetting
from loggers import init_logger
from WinAPI.Device import AudioInterface

root_directory = os.path.abspath(os.curdir)

settings: SpeakerSetting = SpeakerSetting()
interface: AudioInterface = AudioInterface(settings)
logger: logging = init_logger(settings.log_file_path, "speaker")

def exit_program_bcs_err():
    logger.info("Завершение работы программы из-за ошибки...")
    sys.exit(0)
