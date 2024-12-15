import os
import json
import sys
import requests
from pathlib import Path
from PyQt5.QtCore import Qt, QUrl, QSize, QTimer, QStringListModel, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage, QIcon, QColor, QFont
from PyQt5.QtWidgets import QScrollArea, QSlider, QMainWindow, QMessageBox, QMenuBar, QDialog, QColorDialog, QFormLayout, QLineEdit, QMenu, QAction, QListWidgetItem, QListWidget, QTabWidget, QApplication, QWidget, QVBoxLayout, QComboBox, QLabel, QFrame, QHBoxLayout, QFileDialog, QSizePolicy, QSpinBox, QPushButton
from PyQt5.QtWidgets import QApplication, QStyleFactory, QProgressBar
from io import BytesIO
from PIL import Image
from PaintingGenerator import PaintingGenerator
from ResourcePackBuilder import ResourcePackBuilder
from FrameDialog import LoadingDialog, InputDialog, HelpDialog
from FrameWidgets import PackControls, PaintingEditor

class PaintingStudio(QMainWindow):

    def __init__(self):
        super().__init__()
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        layout = QHBoxLayout(self)
        self.central_widget.setLayout(layout)

        # generated stuff
        self.setWindowTitle("Minecraft Painting Studio")
        self.setGeometry(100, 100, 1000, 600)

        menubar = self.menuBar()
        file_menu = menubar.addMenu('File')
        help_menu = menubar.addMenu('Help')

        new_pack_action = QAction('New Pack', self)
        open_draft_action = QAction('Open Draft', self)
        self.save_draft_action = QAction('Save Draft', self)
        new_pack_action.triggered.connect(self.newPack)
        open_draft_action.triggered.connect(self.loadFromFile)
        self.save_draft_action.triggered.connect(self.saveToFile)

        help_action = QAction('Help', self)
        help_action.triggered.connect(self.prog_help)

        file_menu.addAction(new_pack_action)
        file_menu.addAction(open_draft_action)
        file_menu.addAction(self.save_draft_action)
        help_menu.addAction(help_action)

        """ Left Bar """
        self.packConrols = PackControls(self)
        
        """Center Widget"""
        self.paintingEditor = PaintingEditor(self)

        """Main Window"""
        layout.addWidget(self.paintingEditor)
        layout.addWidget(self.packConrols)
        self.setLayout(layout)

        # Set the whole window to accept drops
        self.setButtonEnabled(False)
        self.setAcceptDrops(True)

    def newPack(self):
        # Create and show the input dialog
        dialog = InputDialog(self)
        
        # Check if the dialog was accepted
        if dialog.exec_() == QDialog.Accepted:
            title, description, number, icon = dialog.get_data()
            self.paintingEditor.newPack()
            #remove self. later
            self.packName = title
            packMeta = {
                "pack": {
                    "description": f"{description}",
                    "pack_format": number
                }
            }
            self.packConrols.setPackInfo(title, packMeta, icon)

    def reset(self):
        self.paintingEditor.reset()

    def setButtonEnabled(self, value):
        listFull = self.packConrols.updateButtonEnabled()
        self.save_draft_action.setEnabled(listFull)
        self.packConrols.add_button.setEnabled(value)
        self.paintingEditor.setButtonEnabled(value)
        return

    def loadFromFile(self):
        self.packConrols.loadDraft()

    def saveToFile(self):
        self.packConrols.saveDraft()

    def setCurrentImage(self, file_path):
        self.paintingEditor.setCurrentImage(file_path)

    def setCurrentData(self, paintingName, paintingMetaData):
        self.paintingEditor.setCurrentData(paintingName, paintingMetaData)

    def getCurrentImageData(self):
        return self.paintingEditor.getCurrentImageData()

    def getCurrentImage(self):
        return self.paintingEditor.getCurrentImage()

    def setLockStatus(self, status):
        self.paintingEditor.lock = status

    def getNextImage(self):
        self.setLockStatus(False)
        self.paintingEditor.getNextImage()

    def updateComboBox(self):
        self.paintingEditor.updateComboBox()

    def addToComboBox(self, item):
        if self.paintingEditor.size_combo_box.findText(item) == -1:
            self.paintingEditor.size_combo_box.addItem(item)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        # Get the dropped file path
        if self.packConrols.packCreated == True:
            for file in event.mimeData().urls():
                self.paintingEditor.file_path_stack.append(file)
            self.paintingEditor.init_stack_count = len(self.paintingEditor.file_path_stack)
            self.getNextImage()
        else:
            QMessageBox.information(self, "Pack not Created", f"Please create a pack before importing images.")

    def prog_help(self):
        dialog = HelpDialog(self)
        dialog.exec_()


def set_theme(app):
    desktop = ""
    try:
        gtk_based = [
            "gnome", "lxde", "mate",
            "cinnamon", "ubuntu"
        ]
        desktop = os.environ.get('DESKTOP_SESSION')
        if any(sub in desktop for sub in gtk_based):
            try:
                import subprocess
                result = subprocess.run(
                    ['gsettings', 'get', 'org.gnome.desktop.interface', 'color-scheme'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                theme = result.stdout.strip().lower()
                if 'dark' in theme:
                    app.setStyle("Adwaita-Dark")
                else:
                    app.setStyle("Adwaita")
            except:
                app.setStyle("Adwaita")
    except:
        pass
    current_style = app.style().objectName()
    print(f"Loaded Theme: {current_style} on {desktop}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    set_theme(app)
    window = PaintingStudio()
    #window.setObjectName("Frame")
    window.show()
    window.newPack()
    sys.exit(app.exec_())
