from PySide6.QtWidgets import QItemDelegate, QComboBox

class ComboboxDelegate(QItemDelegate):
    """
    A delegate to add QComboBox in every cell of the given column
    """

    def __init__(self, parent) -> None:
        super().__init__(parent)
        self.parent = parent

    def createEditor(self, parent, option, index) -> QComboBox:
        combobox = QComboBox(parent)
        version_list = []
        for item in index.data():
            if item not in version_list:
                version_list.append(item)

        combobox.addItems(version_list)
        combobox.currentTextChanged.connect(lambda value: self.currentIndexChanged(index, value))
        return combobox

    def setEditorData(self, editor, index) -> None:
        value = index.data()
        if value:
            maxval = len(value)
            editor.setCurrentIndex(maxval - 1)
