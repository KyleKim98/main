import hou,os
from PySide2 import QtWidgets
from . import exporter
from importlib import reload

class UserInputDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(UserInputDialog, self).__init__(parent)
        
        self.setWindowTitle("Choose Directories")
        self.setMinimumSize(400, 150)
        self.setSizeGripEnabled(True)

        # Main layout
        layout = QtWidgets.QVBoxLayout()

        # Directory selection sections
        self.dir1_layout = self.create_directory_input("Scene File:",'E:/MyLibrary/Scenes/Test2/Scene2.usda',True)
        self.dir2_layout = self.create_directory_input("Export Path:",'E:/MyLibrary/Scenes/Test2/export_test/Scene')
        self.dir3_layout = self.create_directory_input("Asset Path:",'E:/MyLibrary')

        # OK & Cancel buttons
        button_layout = QtWidgets.QHBoxLayout()
        self.ok_button = QtWidgets.QPushButton("OK")
        self.cancel_button = QtWidgets.QPushButton("Cancel")
        self.ok_button.clicked.connect(self.ok_clicked)
        self.cancel_button.clicked.connect(self.reject)

        self.dry_run_check = QtWidgets.QCheckBox('Dry run')
        self.dry_run_check.setChecked(True)

        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)

        # Add sections to the layout
        layout.addLayout(self.dir1_layout)
        layout.addLayout(self.dir2_layout)
        layout.addLayout(self.dir3_layout)
        layout.addWidget(self.dry_run_check)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def create_directory_input(self, label_text,default_text,file_select=False):

        layout = QtWidgets.QHBoxLayout()
        label = QtWidgets.QLabel(label_text)
        text_field = QtWidgets.QLineEdit()
        text_field.setText(default_text)
        text_field.setReadOnly(False)        
        browse_button = QtWidgets.QPushButton("Browse")        

        browse_button.clicked.connect(lambda: self.choose_directory(text_field,file_select))

        layout.addWidget(label)
        layout.addWidget(text_field)
        layout.addWidget(browse_button)
        layout.setStretch(1, 1)  

        return layout

    def choose_directory(self, text_field,file_select=False):
        """Handles directory selection and updates the corresponding text field."""
        if file_select:
            file = QtWidgets.QFileDialog.getOpenFileName(self, "Select Scene File")[0]
            if file:
                text_field.setText(file)
        else:
            directory = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Folder")
            if directory:
                text_field.setText(directory)

    def ok_clicked(self):

        self.usd_path = self.dir1_layout.itemAt(1).widget().text()
        self.dest_folder = self.dir2_layout.itemAt(1).widget().text()
        self.asset_path = self.dir3_layout.itemAt(1).widget().text()

        self.dirs = (self.usd_path,self.dest_folder,self.asset_path)
        
        if not self.usd_path or not self.dest_folder or not self.asset_path:
            self.show_warning()
        elif self.dry_run_check.isChecked():
            exporter.copy_usd_and_all_dependencies(self.usd_path, self.dest_folder, self.asset_path)
        else:
            self.show_final_warning()

    def show_warning(self):
        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)

        msg_box = QtWidgets.QMessageBox()
        msg_box.setIcon(QtWidgets.QMessageBox.Warning)
        msg_box.setWindowTitle("Warning")
        msg_box.setText("All directories must be selected!")
        msg_box.setStandardButtons(QtWidgets.QMessageBox.Ok)

        msg_box.exec_()  # Show the warning dialog

    def show_final_warning(self):
        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)

        msg_box = QtWidgets.QMessageBox(self)
        msg_box.setIcon(QtWidgets.QMessageBox.Warning)
        msg_box.setWindowTitle("Are you sure?")
        msg_box.setText("You're about to copy everything. Continue?")
        ok_button = msg_box.addButton(QtWidgets.QMessageBox.Ok)
        msg_box.addButton(QtWidgets.QMessageBox.Cancel)

        ans = msg_box.exec_()

        if ans==1024:
            exporter.copy_usd_and_all_dependencies(self.usd_path, self.dest_folder, self.asset_path,False)


def run():
    reload(exporter)
    global dialog  # Keep reference to prevent garbage collection
    dialog = UserInputDialog(hou.ui.mainQtWindow())
    result = dialog.exec_()
