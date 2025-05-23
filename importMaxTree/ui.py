from PySide2 import QtWidgets
from importlib import reload
import hou,os
from . import importer

hipname = hou.getenv('HIPNAME')
download_dir = 'C:/Users/USER/Downloads/'
class UserInputDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(UserInputDialog, self).__init__(parent)
        
        self.setWindowTitle("Choose Directories")
        self.setMinimumSize(400, 150)
        self.setSizeGripEnabled(True)

        # Main layout
        layout = QtWidgets.QVBoxLayout()

        # Directory selection sections
        self.dir1_layout = self.create_directory_input("FBX Path:")
        self.dir2_layout = self.create_directory_input("Texture Path:")
        self.dir3_layout = self.create_directory_input("Save Path:")

        # OK & Cancel buttons
        button_layout = QtWidgets.QHBoxLayout()
        self.ok_button = QtWidgets.QPushButton("OK")
        self.cancel_button = QtWidgets.QPushButton("Cancel")
        self.ok_button.clicked.connect(self.ok_clicked)
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)

        # Add sections to the layout
        layout.addLayout(self.dir1_layout)
        layout.addLayout(self.dir2_layout)
        layout.addLayout(self.dir3_layout)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        src_dir = download_dir+hipname+'/'
        self.dir1_layout.itemAt(1).widget().setText(src_dir+hipname+'_FBX')
        self.dir2_layout.itemAt(1).widget().setText(src_dir+hipname+'_Maps')
        self.dir3_layout.itemAt(1).widget().setText('$HIP/USD')

    def create_directory_input(self, label_text):

        layout = QtWidgets.QHBoxLayout()
        label = QtWidgets.QLabel(label_text)
        text_field = QtWidgets.QLineEdit()
        text_field.setReadOnly(False)
        browse_button = QtWidgets.QPushButton("Browse")
        
        browse_button.clicked.connect(lambda: self.choose_directory(text_field))

        layout.addWidget(label)
        layout.addWidget(text_field)
        layout.addWidget(browse_button)
        layout.setStretch(1, 1)  

        return layout

    def choose_directory(self, text_field):
        """Handles directory selection and updates the corresponding text field."""
        directory = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Folder")
        if directory:
            text_field.setText(directory)

    def ok_clicked(self):

        dir1 = self.dir1_layout.itemAt(1).widget().text()
        dir2 = self.dir2_layout.itemAt(1).widget().text()
        dir3 = self.dir3_layout.itemAt(1).widget().text()

        self.dirs = (dir1,dir2,dir3)
        
        if not dir1 or not dir2 or not dir3:
            self.show_warning()
        else:
            self.accept()

    def show_warning(self):
        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)

        msg_box = QtWidgets.QMessageBox()
        msg_box.setIcon(QtWidgets.QMessageBox.Warning)
        msg_box.setWindowTitle("Warning")
        msg_box.setText("All directories must be selected!")
        msg_box.setStandardButtons(QtWidgets.QMessageBox.Ok)

        msg_box.exec_()  # Show the warning dialog

def run():
    global dialog
    dialog = UserInputDialog(hou.ui.mainQtWindow())
    result = dialog.exec_()
    reload(importer)
    if result == 1:
        importer.loadfbx(dialog.dirs)

    else:
        hou.ui.displayMessage('unexpected user input',severity=hou.severityType.Warning)