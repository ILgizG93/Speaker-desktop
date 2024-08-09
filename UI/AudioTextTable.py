from PySide6.QtWidgets import QTableView, QHeaderView, QAbstractItemView

from .TableModel import TableModel

class AudioTextTable(QTableView):
    def __init__(self, header, parent=None):
        super().__init__(parent)
        
        self.header = header
        self.column_count = len(self.header)

        self.table_model = TableModel(self, self.header)
        self.setModel(self.table_model)
        self.setColumnHidden(0, True)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.setColumnWidth(2, 180)

    def get_current_row_id(self) -> str:
        try:
            row_id = self.model().index(self.currentIndex().row(), 0).data()
        except AttributeError as err:
            return None
        return row_id