from PySide6.QtWidgets import QTableView, QHeaderView, QAbstractItemView

from .TableModel import TableModel

class BackgroundTable(QTableView):
    def __init__(self, header=('', 'Название'), parent=None):
        super().__init__(parent)
        
        self.header = header
        self.column_count = len(self.header)
        self.setMaximumWidth(340)

        self.table_model = TableModel(self, self.header)
        self.setModel(self.table_model)
        self.setColumnHidden(0, True)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
