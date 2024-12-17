from PyQt5.QtCore import Qt, QUrl, QSize, QTimer, QStringListModel, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage, QIcon, QColor, QFont
from PyQt5.QtWidgets import QScrollArea, QSlider, QMainWindow, QMessageBox, QMenuBar, QDialog, QColorDialog, QFormLayout, QLineEdit, QMenu, QAction, QListWidgetItem, QListWidget, QTabWidget, QApplication, QWidget, QVBoxLayout, QComboBox, QLabel, QFrame, QHBoxLayout, QFileDialog, QSizePolicy, QSpinBox, QPushButton
from PyQt5.QtWidgets import QApplication, QStyleFactory, QProgressBar, QSpacerItem, QCheckBox
import webbrowser

class BatchEditDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Batch Edit")
        self.setModal(True)
        self.setObjectName("Frame")
        layout = QFormLayout()

        layout.addRow(QLabel("Change settings for all paintings in pack.\n"))

        """Detail"""
        detail_layout = QHBoxLayout()
        # CheckBox
        detail_enable = QCheckBox()
        detail_layout.addWidget(detail_enable)
        # Spinner
        self.detail_spin_box = QSpinBox(self)
        self.detail_spin_box.setRange(1, 16)  # Set the valid range (1 to 100)
        self.detail_spin_box.setValue(1)  # Set the initial value
        #self.detail_spin_box.valueChanged.connect(self.requestViewPortDraw)
        self.detail_spin_box.setEnabled(False)
        detail_enable.stateChanged.connect(lambda state: self.setEnable(state, self.detail_spin_box))
        detail_layout.addWidget(self.detail_spin_box)
        layout.addRow("Detail:", detail_layout)


        """Scale Method"""
        scale_layout = QHBoxLayout()
        # CheckBox
        scale_enable = QCheckBox()
        scale_layout.addWidget(scale_enable)
        # Combo box
        self.scale_combo_box = QComboBox(self)
        self.scale_combo_box.addItems(["Stretch", "Fit", "Crop"])
        self.scale_combo_box.setEnabled(False)
        scale_enable.stateChanged.connect(lambda state: self.setEnable(state, self.scale_combo_box))
        scale_layout.addWidget(self.scale_combo_box)
        layout.addRow("Scale Method:", scale_layout)

        """Frame"""
        frame_layout = QHBoxLayout()
        # CheckBox
        frame_enable = QCheckBox()
        frame_layout.addWidget(frame_enable)
        # Combo box
        self.frame_combo_box = QComboBox(self)
        self.frame_combo_box.addItems(["Default", "None"])
        self.frame_combo_box.setEnabled(False)
        frame_enable.stateChanged.connect(lambda state: self.setEnable(state, self.frame_combo_box))
        frame_layout.addWidget(self.frame_combo_box)
        layout.addRow("Frame:", frame_layout)

        """Color"""
        color_layout = QHBoxLayout()
        self.color = "#000000"
        # CheckBox
        color_enable = QCheckBox()
        color_layout.addWidget(color_enable)
        # Combo box
        self.color_button = QPushButton("Choose")
        self.color_button.setEnabled(False)
        color_enable.stateChanged.connect(lambda state: self.setEnable(state, self.color_button))
        color_layout.addWidget(self.color_button)
        layout.addRow("Background Color:", color_layout)

        button_layout = QHBoxLayout()
        self.submit_button = QPushButton("Submit")
        self.submit_button.setEnabled(False)
        self.submit_button.clicked.connect(self.submit)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.submit_button)
        button_layout.addWidget(self.cancel_button)
        layout.addRow(button_layout)

        self.setLayout(layout)

    def setEnable(self, state, settingObj):
        settingObj.setEnabled(state)
        if (self.detail_spin_box.isEnabled()
        or self.scale_combo_box.isEnabled()
        or self.frame_combo_box.isEnabled()
        or self.color_button.isEnabled()):
            self.submit_button.setEnabled(True)
        else:
            self.submit_button.setEnabled(False)

    def submit(self):
        print(self.get_data())
        self.accept()

    def get_data(self):
        data = {
            'detail': False,
            'scale_method': False,
            'frame': False,
            'background_color': False
        }
        if self.detail_spin_box.isEnabled():
            data['detail'] = self.detail_spin_box.value()
        if  self.scale_combo_box.isEnabled():
            data['scale_method'] = self.detail_spin_box.value()
        if self.frame_combo_box.isEnabled():
            data['frame'] = self.frame_combo_box.currentText()
        if self.color_button.isEnabled():
            data['background_color'] = self.color
        return data

class HelpDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Help")
        self.setModal(True)
        self.setObjectName("Frame")
        self.setFixedSize(300, 100)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("WIP"))

class LoadingDialog(QDialog):
    # Define a signal to update progress
    update_progress_signal = pyqtSignal(int)

    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName("Frame")
        # Initialize the dialog window
        self.setWindowTitle("Opening Draft")
        self.setModal(True)
        self.setFixedSize(300, 100)

        self.setWindowFlags(Qt.Dialog)

        # Create the progress bar
        self.progressBar = QProgressBar(self)

        # Set layout for the dialog
        layout = QVBoxLayout(self)
        layout.addWidget(self.progressBar)

        # Connect the signal to the slot method
        self.update_progress_signal.connect(self.update_progress)

    def update_progress(self, value):
        """Slot to update the progress bar"""
        self.progressBar.setValue(value)

    def show_loading(self, value):
        """Show the dialog (non-modal)"""
        self.progressBar.setRange(0, value)
        self.progressBar.setValue(0)
        self.show()  # This will show the dialog non-modally

    def close_dialog(self):
        """Method to close the dialog"""
        self.close()  # Close the dialog

class InputDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.icon = None
        self.setWindowTitle("Create New Pack")
        self.setModal(True)
        self.setObjectName("Frame")
        # Create form layout
        layout = QFormLayout()
        packFormatLayout = QHBoxLayout()

        # Create input fields
        self.title_input = QLineEdit("PaintingPack")
        self.description_input = QLineEdit("My Painting Pack")
        self.number_input = QSpinBox()
        self.number_input.setValue(46)      # Most up to date pact format as of relase
        self.number_input.setRange(4, 256)  # Surely they add more paintings before Format 256
        packFormatLayout.addWidget(self.number_input)
        self.packFormatLink = QPushButton("Help")
        packFormatLayout.addWidget(self.packFormatLink)
        self.iconButton = QPushButton("Set Pack Icon")
        self.iconButton.clicked.connect(self.setIcon)

        # Add fields to the layout
        layout.addRow("Title:", self.title_input)
        layout.addRow("Description:", self.description_input)
        layout.addRow("Pack Format:", packFormatLayout)
        layout.addRow(self.iconButton)

        # Create Ok and Cancel buttons
        self.ok_button = QPushButton("Ok")
        self.cancel_button = QPushButton("Cancel")

        # Add buttons to the layout
        buttonLayout = QHBoxLayout()
        buttonLayout.addWidget(self.ok_button)
        buttonLayout.addWidget(self.cancel_button)
        layout.addRow(buttonLayout)

        # Set dialog layout
        self.setLayout(layout)

        # Connect buttons to functions
        self.packFormatLink.clicked.connect(self.packFormat_Info)
        self.ok_button.clicked.connect(self.on_ok_button_clicked)
        self.cancel_button.clicked.connect(self.reject)

    def packFormat_Info(self):
        webbrowser.open_new_tab("https://minecraft.wiki/w/Pack_format#List_of_resource_pack_formats")

    def get_data(self):
        # Return the data entered by the user
        return self.title_input.text(), self.description_input.text(), self.number_input.value(), self.icon

    def on_ok_button_clicked(self):
        # Validate required fields before accepting the form
        if not self.title_input.text().strip() or not self.description_input.text().strip():
            QMessageBox.information(self, "Pack not Created", "You need a Title and Description")
        else:
            self.accept()  # Proceed with accepting the form if validation passes

    def setIcon(self):
        lastText = self.iconButton.text()
        self.iconButton.setText("Set Pack Icon")
        file_name, _ = QFileDialog.getOpenFileName(self, 'Select Pack Icon', '', 'Images (*.png *.xpm *.jpg *.jpeg *.bmp *.gif)')
        if file_name:
            self.icon = file_name
            self.iconButton.setText("Icon Set!")
        else:
            self.iconButton.setText(lastText)
