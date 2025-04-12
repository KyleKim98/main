
from PySide2 import QtWidgets, QtCore, QtGui
import hou, os
from . import utils

class DynamicInputDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(DynamicInputDialog, self).__init__(parent)

        self.setWindowTitle("Dynamic Key-Value Inputs in Houdini")
        self.setMinimumWidth(600)

        # Main layout
        self.layout = QtWidgets.QVBoxLayout()

        # Directory chooser
        self.dir_layout = QtWidgets.QHBoxLayout()
        self.dir_label = QtWidgets.QLabel("Selected Directory:")
        self.dir_layout.addWidget(self.dir_label)

        self.dir_input = QtWidgets.QLineEdit(self)
        self.dir_input.setPlaceholderText("No directory selected")
        self.dir_layout.addWidget(self.dir_input)

        self.dir_button = QtWidgets.QPushButton("Browse")
        self.dir_button.clicked.connect(self.choose_directory)
        self.dir_layout.addWidget(self.dir_button)

        self.layout.addLayout(self.dir_layout)

        # Preset Container
        self.preset_layout = QtWidgets.QHBoxLayout()
        self.preset_input = QtWidgets.QComboBox(self)
        self.preset_input.addItems(['Kitbash', 'Maxtree'])
        self.preset_input.setCurrentIndex(0)
        self.preset_layout.addWidget(self.preset_input)
        self.layout.addLayout(self.preset_layout)

        self.preset_input.currentIndexChanged.connect(lambda:self.changePreset())

        # Number of fields control (manual input + "+" and "-" buttons)
        self.num_layout = QtWidgets.QHBoxLayout()
        self.num_label = QtWidgets.QLabel("Number of Input Pairs:")
        self.num_layout.addWidget(self.num_label)

        self.num_input = QtWidgets.QLineEdit("5")  # Default to 5 fields
        self.num_input.setValidator(QtGui.QIntValidator(0, 100))  # Allows only numbers
        self.num_input.setFixedWidth(40)
        self.num_input.setAlignment(QtCore.Qt.AlignCenter)
        self.num_input.editingFinished.connect(self.manual_field_update)
        self.num_layout.addWidget(self.num_input)

        self.minus_button = QtWidgets.QPushButton("−")
        self.minus_button.clicked.connect(self.decrease_fields)
        self.num_layout.addWidget(self.minus_button)

        self.plus_button = QtWidgets.QPushButton("+")
        self.plus_button.clicked.connect(self.increase_fields)
        self.num_layout.addWidget(self.plus_button)

        self.layout.addLayout(self.num_layout)

        # Container for dynamic input fields
        self.input_container = QtWidgets.QWidget()
        self.input_layout = QtWidgets.QVBoxLayout(self.input_container)
        self.layout.addWidget(self.input_container)

        # Button to retrieve values
        self.get_values_button = QtWidgets.QPushButton("Run", self)
        self.get_values_button.clicked.connect(self.get_values)  # Closes dialog on click
        self.get_values_button.setShortcut('Return')
        self.layout.addWidget(self.get_values_button)

        self.setLayout(self.layout)

        # Storage for dynamically created input fields
        self.input_pairs = []

        # Initialize with 5 fields
        self.update_fields(5)

        default_keys = ['albedo', 'roughness', 'normal', 'translucency', 'opacity']

        try:
            for enum, i in enumerate(self.input_pairs):
                self.input_pairs[enum][0].setText(default_keys[enum])
                self.input_pairs[enum][2].setText('jpg')
        except IndexError:
            pass

        # set colorspace to Raw for Roughness,Noraml and Opacity
        self.input_pairs[1][1].setCurrentIndex(1)
        self.input_pairs[2][1].setCurrentIndex(1)
        self.input_pairs[4][1].setCurrentIndex(1)

        self.changePreset()

    def changePreset(self):
        preset_name = self.preset_input.currentText()

        if preset_name == 'Kitbash':
            self.update_fields(8)
            kitbash_keys = ['basecolor', 'roughness', 'normal', 'metallic', 'opacity','ao','height','refraction']

            for enum,i in enumerate(kitbash_keys):
                self.input_pairs[enum][0].setText(i)
                self.input_pairs[enum][2].setText('png')

                if i == 'basecolor':
                    self.input_pairs[1][1].setCurrentIndex(0)
                else:
                    self.input_pairs[enum][1].setCurrentIndex(1)
        elif preset_name == 'Maxtree':
            self.update_fields(5)
            maxtree_keys = ['albedo', 'roughness', 'normal', 'translucency', 'opacity']

            try:
                for enum, i in enumerate(self.input_pairs):
                    self.input_pairs[enum][0].setText(maxtree_keys[enum])
                    self.input_pairs[enum][2].setText('jpg')
            except IndexError:
                pass

            # set colorspace to Raw for Roughness,Noraml and Opacity
            self.input_pairs[1][1].setCurrentIndex(1)
            self.input_pairs[2][1].setCurrentIndex(1)
            self.input_pairs[4][1].setCurrentIndex(1)

    def choose_directory(self):
        """Opens a directory chooser and sets the selected path."""
        dir_path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory")
        if dir_path:
            self.dir_input.setText(dir_path)

    def increase_fields(self):
        """Increases the number of input pairs."""
        self.update_fields(len(self.input_pairs) + 1)

    def decrease_fields(self):
        """Decreases the number of input pairs."""
        if len(self.input_pairs) > 0:
            self.update_fields(len(self.input_pairs) - 1)

    def manual_field_update(self):
        """Updates fields when the user manually types a number."""
        try:
            num_fields = int(self.num_input.text())
            self.update_fields(num_fields)
        except ValueError:
            pass  # Ignore invalid inputs

    def update_fields(self, num_pairs):
        """Updates the number of dynamically created input pairs."""
        num_pairs = max(0, num_pairs)  # Ensure it's not negative

        # Clear extra inputs if reducing
        while len(self.input_pairs) > num_pairs:
            pair = self.input_pairs.pop()
            pair[0].deleteLater()
            pair[1].deleteLater()
            pair[2].deleteLater()

        # Add new fields if increasing
        while len(self.input_pairs) < num_pairs:
            row_layout = QtWidgets.QHBoxLayout()
            
            # Pattern (Key) Input
            pattern_input = QtWidgets.QLineEdit(self)
            pattern_input.setPlaceholderText("Key")
            row_layout.addWidget(pattern_input)

            # Colorspace Dropdown
            colorspace_input = QtWidgets.QComboBox(self)
            colorspace_input.addItems(['ACEScg', 'Raw'])
            row_layout.addWidget(colorspace_input)
                    
            # Extension (Value) Input
            extension_input = QtWidgets.QLineEdit(self)
            extension_input.setPlaceholderText("Value")
            row_layout.addWidget(extension_input)

            self.input_layout.addLayout(row_layout)
            self.input_pairs.append((pattern_input, colorspace_input, extension_input))

        # Update number input field
        self.num_input.setText(str(num_pairs))

        # Force layout update
        self.input_container.setLayout(self.input_layout)
        self.input_container.adjustSize()
        self.adjustSize()

    def show_warning(self,message):
        #app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)

        msg_box = QtWidgets.QMessageBox()
        msg_box.setIcon(QtWidgets.QMessageBox.Warning)
        msg_box.setWindowTitle("Warning")
        msg_box.setText(message)
        msg_box.setStandardButtons(QtWidgets.QMessageBox.Ok)

        msg_box.exec_()  # Show the warning dialog

    def get_values(self):

        if not self.dir_input.text():
            self.show_warning("Directory cannot be empty!")
            return

        for enum_i, i in enumerate(self.input_pairs):
            for enum_j, j in enumerate(i):
                if isinstance(j, QtWidgets.QComboBox):
                    continue
                elif not j.text():
                    QtWidgets.QMessageBox.warning(self, "Warning", f"Input {enum_j} at line {enum_i} is empty")
                    return

        self.values = [
            {"pattern": key.text(), "colorspace": colorspace.currentText(), "extension": extension.text()}
            for key, colorspace, extension in self.input_pairs
        ]
        self.directory = self.dir_input.text()

        return self.accept()


def run():
    """Creates and executes the input dialog."""
    global dialog
    dialog = DynamicInputDialog(hou.ui.mainQtWindow())
    result = dialog.exec_()

    if result == 1:
        print(dialog.directory)
        print(dialog.values)
        setup(dialog.directory,dialog.values)


def makeExporter(tex_type,input_color,extension):
    pattern_node = topnet.createNode('filepattern')
    pattern = utils.BtF(tex_path+'*'+tex_type+'.'+extension)
    pattern_node.parm('pattern').set(pattern)
    pattern_node.setName(tex_type)

    generic_node = topnet.createNode('genericgenerator')
    command_parm = generic_node.parm('pdg_command')
    command = 'maketx -u --oiio --checknan --filter lanczos3 --colorconvert "' +input_color+ '" "ACEScg" `@pdg_input` ' +tex_path+'`@filename``@extension`'
    command_parm.set(command)
    generic_node.setInput(0,pattern_node)

def setup(directory,value):

    global tex_path
    global obj
    global topnet

    tex_path = utils.tailSlash(directory)

    obj = hou.node('/obj')
    topnet = obj.createNode('topnet')
    topnet.node('localscheduler').parm('maxprocsmenu').set(-1)

    for i in value:
        makeExporter(i['pattern'],i['colorspace'],i['extension'])    

    merge_node = topnet.createNode('merge')

    for enum,i in enumerate(topnet.children()):
        if i.type().name() == 'genericgenerator':
            merge_node.setInput(enum,i)

    topnet.layoutChildren()  
