from typing import Optional

from PySide6.QtWidgets import QTableView, QHeaderView, QAbstractItemView, QItemDelegate
from PySide6.QtCore import QObject, Qt, QObject

from .TableModel import TableModel

class ScheduleTable(QTableView):
    def __init__(self, settings, header, parent=None):
        super().__init__(parent)
        
        self.settings = settings
        self.header = header
        self.column_count = len(self.header)

        self.table_model = TableModel(self, self.header)
        self.setModel(self.table_model)
        self.setColumnHidden(0, True)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        self.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.Stretch)
        self.horizontalHeader().setSectionResizeMode(8, QHeaderView.ResizeMode.Fixed)
        self.horizontalHeader().setSectionResizeMode(9, QHeaderView.ResizeMode.Fixed)
        self.horizontalHeader().setSectionResizeMode(10, QHeaderView.ResizeMode.Fixed)
        self.setColumnWidth(8, 54)
        self.setColumnWidth(9, 54)
        self.setColumnWidth(10, 54)
        self.setItemDelegate(AlignDelegate((2, 3, 4, 6, 8, 9, 10)))
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)


class AlignDelegate(QItemDelegate):
    def __init__(self, columns, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.columns = columns

    def paint(self, painter, option, index) -> None:
        if index.column() in self.columns:
            option.displayAlignment = Qt.AlignmentFlag.AlignCenter
        else:
            option.displayAlignment = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        QItemDelegate.paint(self, painter, option, index)
