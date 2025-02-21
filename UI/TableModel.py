from PySide6.QtCore import Qt, QAbstractTableModel

class TableModel(QAbstractTableModel):
    def __init__(self, parent, header, data = [], centered_columns = [], checkable_columns=None, combobox_columns=None, editable_columns=None) -> None:
        super().__init__(parent)
        self._data = data
        self._header = header
        self._centered_columns = centered_columns
        if checkable_columns is None:
            checkable_columns = []
        elif isinstance(checkable_columns, int):
            checkable_columns = [checkable_columns]
        self._checkable_columns = set(checkable_columns)
        if combobox_columns is None:
            combobox_columns = []
        elif isinstance(combobox_columns, int):
            combobox_columns = [combobox_columns]
        self._combobox_columns = set(combobox_columns)
        if editable_columns is None:
            editable_columns = []
        elif isinstance(editable_columns, int):
            editable_columns = [editable_columns]
        self._editable_columns = set(editable_columns)

    def setColumnCheckable(self, column, checkable=True) -> None:
        if checkable:
            self._checkable_columns.add(column)
        else:
            self._checkable_columns.discard(column)
        self.dataChanged.emit(self.index(0, column), self.index(self.rowCount() - 1, column))

    def rowCount(self, index) -> int:
        return len(self._data)

    def columnCount(self, index) -> int:
        return len(self._header)

    def flags(self, index):
        flags = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
        if index.column() in self._checkable_columns:
            flags |= Qt.ItemFlag.ItemIsUserCheckable
        if index.column() in [set(self._editable_columns) | set(self._combobox_columns)]:
            flags |= Qt.ItemFlag.ItemIsEditable
        return flags

    def data(self, index, role):
        if not index.isValid():
           return None
        if role == Qt.ItemDataRole.CheckStateRole and index.column() in self._checkable_columns:
            value = self._data[index.row()][index.column()]
            return Qt.CheckState.Checked if value else Qt.CheckState.Unchecked
        elif index.column() not in (self._checkable_columns) and index.column() not in (5,) and role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            return self._data[index.row()][index.column()]
        elif role == Qt.ItemDataRole.TextAlignmentRole and index.column() in self._centered_columns:
            return Qt.AlignmentFlag.AlignCenter
        elif role == Qt.ItemDataRole.DecorationRole and index.column() in self._checkable_columns:
            return Qt.CursorShape.PointingHandCursor
    
    def headerData(self, col, orientation, role):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self._header[col]
        return None

    def setData(self, index, value, role = Qt.ItemDataRole.EditRole) -> bool:
        if (role == Qt.ItemDataRole.CheckStateRole and index.column() in self._checkable_columns):
                self._data[index.row()][index.column()] = bool(value)
                self.dataChanged.emit(index, index)
                return True
        if value is not None and role == Qt.ItemDataRole.EditRole:
            self._data[index.row()][index.column()] = value
            self.dataChanged.emit(index, index)
            return True
        return False

    def setItems(self, items) -> None:
        self.beginResetModel()
        self._data = items
        self.endResetModel()
