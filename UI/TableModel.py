import operator
from PySide6.QtCore import Qt, QAbstractTableModel, SIGNAL

class TableModel(QAbstractTableModel):
    def __init__(self, parent, header, data=[], *args):
        QAbstractTableModel.__init__(self, parent, *args)
        self._header = header
        self._data = data

    def setItems(self, items):
        self.beginResetModel()
        self._data = items
        self.endResetModel()

    def rowCount(self, parent=None):
        return (0, len(self._data))[self._data is not None]
    
    def columnCount(self, parent=None):
        return (0, len(self._header))[len(self._header) > 0]
    
    def headerData(self, col, orientation, role):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self._header[col]
    
    def data(self, index, role):
        if not index.isValid():
            return None
        elif role == Qt.ItemDataRole.DisplayRole:
            return self._data[index.row()][index.column()]

    def insertRows(self, position, rows, QModelIndex, parent):
        self.beginResetModel()
        default_row = ['']*len(self._header)
        [self._data.insert(position, default_row) for _ in range(rows)]
        self.endResetModel()

    def removeRows(self, position, rows):
        self.beginResetModel()
        for _ in range(rows):
            del(self._data[position])
        self.endResetModel()
    
    def sort(self, col, order):
        global current_sort
        self.emit(SIGNAL("layoutAboutToBeChanged()"))
        self._data = sorted(self._data, key=operator.itemgetter(col))
        if order == Qt.SortOrder.DescendingOrder:
            self._data.reverse()
        self.emit(SIGNAL("layoutChanged()"))
        current_sort = [col, order]
