import os
from PySide6.QtCore import QDir
from PySide6.QtGui import QFontDatabase

class RobotoFont(QFontDatabase):
    def __init__(self):
        super().__init__()

        self.load_font_from_dir(os.fspath('fonts/Roboto'))
        self.styles("Roboto")

    @staticmethod
    def load_font_from_dir(directory):
        families = set()
        for fi in QDir(directory).entryInfoList(["*.ttf"]):
            _id = QFontDatabase.addApplicationFont(fi.absoluteFilePath())
            families |= set(QFontDatabase.applicationFontFamilies(_id))
        return families

    def get_font(self, size: int=12):
        return self.font("Roboto", "Regular", size)
