from PyQt5.QtCore import Qt, QUrl, QSize, QTimer, QStringListModel, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage, QIcon, QColor, QFont
from PyQt5.QtWidgets import QScrollArea, QSlider, QMainWindow, QMessageBox, QMenuBar, QDialog, QColorDialog, QFormLayout, QLineEdit, QMenu, QAction, QListWidgetItem, QListWidget, QTabWidget, QApplication, QWidget, QVBoxLayout, QComboBox, QLabel, QFrame, QHBoxLayout, QFileDialog, QSizePolicy, QSpinBox, QPushButton
from PyQt5.QtWidgets import QApplication, QStyleFactory, QProgressBar, QSpacerItem, QCheckBox, QTextBrowser
import webbrowser
import json
import sys
import os

class SaveChangesDialog():
    def __init__(self, parent, changesSaved):
        self.reply = QMessageBox.No
        if not changesSaved:
            self.reply = QMessageBox.question(parent, 'Changes Unsaved', 'Do you want save the the current pack as a draft for future editing?', QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, QMessageBox.Cancel)

    def getReply(self):
        return self.reply

class BatchEditDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
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
        self.backgroundColor = "#000000"
        # CheckBox
        color_enable = QCheckBox()
        color_layout.addWidget(color_enable)
        # Combo box
        self.color_button = QPushButton("Choose")
        self.color_button.clicked.connect(self.showColorDialog)
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
        data = self.get_data()
        settings = ""
        if data['detail'] != False:
            settings += f"    Detail: {data['detail']}\n"
        if  data['scale_method'] != False:
            settings += f"    Scale Method: {data['scale_method']}\n"
        if data['frameName'] != False:
            settings += f"    Frame: {data['frameName']}\n"
        if data['background_color'] != False:
            settings += f"    Background Color: {data['background_color']}\n"
        reply = QMessageBox.question(self.parent, 'Submit Batch Job?', f'This will apply the following settings to every painting in the pack:\n\n{settings}\nThis cannot be undone. Do you wish to continue?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.accept()

    def get_data(self):
        data = {
            'detail': False,
            'scale_method': False,
            'frameName': False,
            'background_color': False
        }
        if self.detail_spin_box.isEnabled():
            data['detail'] = self.detail_spin_box.value()
        if  self.scale_combo_box.isEnabled():
            data['scale_method'] = self.scale_combo_box.currentText()
        if self.frame_combo_box.isEnabled():
            data['frameName'] = self.frame_combo_box.currentText()
        if self.color_button.isEnabled():
            data['background_color'] = self.backgroundColor
        return data

    def showColorDialog(self):
        # Open the QColorDialog
        color = QColorDialog.getColor(QColor(self.backgroundColor))
        if color.isValid():
            # Update the label with the chosen color
            self.backgroundColor = color.name()
        self.requestViewPortDraw()

class HelpDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle('Help')
        self.setMinimumHeight(400)
        self.setMinimumWidth(600)
        layout = QVBoxLayout(self)
        self.tab_widget = QTabWidget(self)
        with open(self.resourcePath('src', 'help.json'), 'r') as file:
            help_pages = json.load(file)
        for page in help_pages:
            self.addPage(page, help_pages[page])
        layout.addWidget(self.tab_widget)
        self.setLayout(layout)

    def addPage(self, page_name, html):
        content = QTextBrowser()
        content.setOpenLinks(True)
        content.setOpenExternalLinks(True)
        content.setHtml(html)
        self.tab_widget.addTab(content, page_name)

    def resourcePath(self, folder, file):
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(__file__)
        return os.path.join(base_path, folder, file)

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
    def __init__(self, parent, currData=False):
        super().__init__(parent)
        self.icon = None
        self.setWindowTitle("Create New Pack")
        self.setModal(True)
        self.setObjectName("Frame")
        # Create form layout
        layout = QFormLayout()
        packFormatLayout = QHBoxLayout()
        if not currData:
            currData = {
                'title': "PaintingPack",
                'icon': None,
                'meta': {
                    "pack": {
                        "description": "My Painting Pack",
                        "pack_format": 46
                    }
                }
            }

        # Create input fields
        self.title_input = QLineEdit(currData['title'])
        self.title_input.textChanged.connect(self.feild_validation)
        self.description_input = QLineEdit(currData['meta']['pack']['description'])
        self.description_input.textChanged.connect(self.feild_validation)
        self.number_input = QSpinBox()
        self.number_input.setValue(currData['meta']['pack']['pack_format'])      # Most up to date pact format as of relase
        self.number_input.setRange(4, 65535)  # Surely they add more paintings before Format 65535
        packFormatLayout.addWidget(self.number_input)
        self.packFormatLink = QPushButton("Help")
        packFormatLayout.addWidget(self.packFormatLink)
        if currData['icon'] != None:
            print(currData['icon'])
            self.iconButton = QPushButton("Icon Set!")
            self.icon = currData['icon']
        else:
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
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

    def packFormat_Info(self):
        webbrowser.open_new_tab("https://minecraft.wiki/w/Pack_format#List_of_resource_pack_formats")

    def get_data(self):
        # Return the data entered by the user
        return self.title_input.text(), self.description_input.text(), self.number_input.value(), self.icon

    def feild_validation(self):
        if not self.title_input.text().strip() or not self.description_input.text().strip():
            self.ok_button.setEnabled(False)
        else:
            self.ok_button.setEnabled(True)

    def setIcon(self):
        lastText = self.iconButton.text()
        self.iconButton.setText("Set Pack Icon")
        file_name, _ = QFileDialog.getOpenFileName(self, 'Select Pack Icon', '', 'Images (*.png *.xpm *.jpg *.jpeg *.bmp *.gif)')
        if file_name:
            self.icon = file_name
            self.iconButton.setText("Icon Set!")
        else:
            self.iconButton.setText(lastText)
