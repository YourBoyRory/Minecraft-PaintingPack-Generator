import os
import json
import sys
import requests
import re
import traceback
from pathlib import Path
from PyQt5.QtCore import Qt, QUrl, QSize, QTimer, QStringListModel, pyqtSignal, QThread
from PyQt5.QtGui import QPixmap, QImage, QIcon, QColor, QFont, QKeySequence
from PyQt5.QtWidgets import QScrollArea, QSlider, QMainWindow, QMessageBox, QMenuBar, QDialog, QColorDialog, QFormLayout, QLineEdit, QMenu, QAction, QListWidgetItem, QListWidget, QTabWidget, QApplication, QWidget, QVBoxLayout, QComboBox, QLabel, QFrame, QHBoxLayout, QFileDialog, QSizePolicy, QSpinBox, QPushButton
from PyQt5.QtWidgets import QApplication, QStyleFactory, QProgressBar, QShortcut
from io import BytesIO
from PIL import Image
from PaintingGenerator import PaintingGenerator
from ResourcePackBuilder import ResourcePackBuilder
from FrameDialog import LoadingDialog, InputDialog, HelpDialog, BatchEditDialog, SaveChangesDialog, MessageDialog
from FrameWidgets import PackControls, PaintingEditor

# Version Information
VER_STRING = "v1.5.0"
PSON_VER = 1

def ResourcePath(folder, file):
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(__file__)
    return os.path.join(base_path, folder, file)

class UpdateCheckWorker(QThread):
    progress = pyqtSignal(str, str, object, str, int)

    def setAutoUpdateMode(self, autoCheckup=True):
        self.autoCheckup = autoCheckup

    def run(self):
        self.progress.emit("", "", None, "Checking for updates...", 15000)
        QApplication.processEvents()
        token=False
        url = f"https://api.github.com/repos/YourBoyRory/Minecraft-PaintingPack-Generator/releases/latest"
        headers = {"Authorization": f"token {token}"} if token else {}

        try:
            response = requests.get(url, headers=headers)
            status_code = response.status_code
        except:
            status_code = 418

        if status_code == 200:
            release = response.json()
            latest_url = release['html_url']
            latest_verStr = release['tag_name']
            latest_body = release['body']
            latest_version = tuple(map(int, re.sub(r'[^0-9.]', '', latest_verStr).split(".")))
            current_version = tuple(map(int, re.sub(r'[^0-9.]', '', VER_STRING).split(".")))
            if latest_version > current_version:
                msg_title="Update Available"
                msg_body=f"""<b>A new version is available!</b><br>
                <p style=\"color: #A6A6A6;\">{latest_body.split('\r\n',1)[1].replace('\r\n','<br>')}</p>
                Download {latest_verStr}:<br> <a href='{latest_url}'>{latest_url}</a>
                """
                self.progress.emit(msg_title, msg_body, QMessageBox.Information, "Update Available! [Help] > [Check for Updates]", 6000)
            else:
                self.progress.emit("","", None, "You are up to date!", 2000)
        else:
            if not self.autoCheckup:
                msg_title="Update Check Failed"
                msg_body=f"""<b>Update Check Failed!</b><br><br>
                    Failed to check updates, maybe you have no internet?
                    <p style=\"color: #A6A6A6;\">HTTP Status: {status_code}</p>
                """
                self.progress.emit(msg_title, msg_body, QMessageBox.Warning, f"Update Check Failed - Status: {status_code}", 6000)
            else:
                self.progress.emit("","", None, f"Update Check Failed - Status: {status_code}", 6000)
        if self.autoCheckup:
            self.autoCheckup = False

class PaintingStudio(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setObjectName("Frame")
        self.central_widget = QWidget()
        self.central_widget.setObjectName("Frame")
        self.setCentralWidget(self.central_widget)
        layout = QHBoxLayout(self)
        self.central_widget.setLayout(layout)

        # Update Thread
        self.updateChecker = UpdateCheckWorker()
        self.updateChecker.progress.connect(self.setUpdateStatus)
        self.updateChecker.setAutoUpdateMode(True)

        # generated stuff
        self.setWindowTitle(f"Minecraft Painting Studio - {VER_STRING}")
        self.setWindowIcon(QIcon(ResourcePath("assets", "icon.png")))
        self.setGeometry(100, 100, 1000, 600)


        """Menu Bar"""
        menubar = self.menuBar()

        #File Menu
        file_menu = menubar.addMenu('File')
        new_pack_action = QAction('New Pack', self)
        new_pack_action.triggered.connect(self.makeNewPack)
        file_menu.addAction(new_pack_action)
        open_draft_action = QAction('Open Draft', self)
        open_draft_action.triggered.connect(self.loadFromFile)
        file_menu.addAction(open_draft_action)
        self.save_draft_as_action = QAction('Save Draft As', self)
        self.save_draft_as_action.triggered.connect(self.saveToFile)
        file_menu.addAction(self.save_draft_as_action)
        self.save_draft_action = QAction('Save', self)
        self.save_draft_action.triggered.connect(self.saveExisting)
        file_menu.addAction(self.save_draft_action)

        edit_menu = menubar.addMenu('Edit')
        self.edit_pack_info = QAction('Edit Pack Info', self)
        self.edit_pack_info.triggered.connect(self.editPackInfo)
        edit_menu.addAction(self.edit_pack_info)

        tool_menu = menubar.addMenu('Tools')
        self.batch_edit_action = QAction('Batch Edit', self)
        self.batch_edit_action.triggered.connect(self.batchEdit)
        tool_menu.addAction(self.batch_edit_action)

        # Help Menu
        help_menu = menubar.addMenu('Help')
        help_action = QAction('Help', self)
        help_action.triggered.connect(self.prog_help)
        help_menu.addAction(help_action)
        update_action = QAction('Check for Updates', self)
        update_action.triggered.connect(self.checkForUpdates)
        help_menu.addAction(update_action)

        """ Left Bar """
        self.packConrols = PackControls(self)

        """Center Widget"""
        self.paintingEditor = PaintingEditor(self)

        """Main Window"""
        layout.addWidget(self.paintingEditor)
        layout.addWidget(self.packConrols)
        self.setLayout(layout)

        self.saveShortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        self.saveShortcut.activated.connect(self.saveExisting)

        # Set the whole window to accept drops
        self.setButtonEnabled(False)
        #self.setAcceptDrops(True)

    ## Frame Code ##

    def closeEvent(self, event):
        dialog = SaveChangesDialog(self, self.packConrols.changesSaved)
        reply = dialog.getReply()
        if reply == QMessageBox.Yes:
            self.saveExisting()
            event.accept()
        elif reply == QMessageBox.No:
            event.accept()
        else:
            event.ignore()

    ## Menu Bar ##

    def setUpdateStatus(self, status_window_title, status_window_body, status_window_type, status_toast, status_toast_wait):
        if status_toast != "":
            self.notify(status_toast, status_toast_wait)
        if status_window_title != "" or status_window_body != "":
            msg_title=status_window_title
            msg_body=status_window_body
            msg_box = MessageDialog(self, msg_body, msg_title, status_window_type)

    def checkForUpdates(self):
        self.updateChecker.start()

    def batchEdit(self):
        dialog = BatchEditDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            new_draft = self.packConrols.used_paintings
            for painting in new_draft:
                if data['detail'] != False:
                    new_draft['paintings'][painting]['detail'] = data['detail']
                if  data['scale_method'] != False:
                    new_draft['paintings'][painting]['scale_method'] = data['scale_method']
                if data['frameName'] != False:
                    if data['frameName'] == "Default":
                        new_draft['paintings'][painting]['frameName'] = painting
                    else:
                        new_draft['paintings'][painting]['frameName'] = "None"
                if data['background_color'] != False:
                    new_draft['paintings'][painting]['background_color'] = data['background_color']
            self.packConrols.loadDraft(new_draft)

    def convert_pson(self):
        pson = {}
        self.packConrols.convert_pson(pson)

    def prog_help(self):
        dialog = HelpDialog(self)
        dialog.exec_()

    def editPackInfo(self, packData=None):
        if packData == None:
            packData = self.packConrols.packData
        dialog = InputDialog(self, packData)
        if dialog.exec_() == QDialog.Accepted:
            title, description, number, icon = dialog.get_data()
            self.paintingEditor.newPack()
            #remove self. later
            self.packName = title
            new_packData = {
                'pson_version': PSON_VER,
                'title': title,
                'icon': icon,
                'meta': {
                    "pack": {
                        "description": f"{description}",
                        "pack_format": number
                    }
                }
            }
            self.packConrols.setPackInfo(new_packData)
            self.paintingEditor.reset()


    def makeNewPack(self):
        dialog = SaveChangesDialog(self, self.packConrols.changesSaved)
        reply = dialog.getReply()
        if reply == QMessageBox.Yes:
            self.saveExisting()
            pass
        elif reply == QMessageBox.No:
            pass
        else:
            return

        # Create and show the input dialog
        dialog = InputDialog(self)

        # Check if the dialog was accepted
        if dialog.exec_() == QDialog.Accepted:
            title, description, number, icon = dialog.get_data()
            #remove self. later
            self.packName = title
            packData = {
                'pson_version': PSON_VER,
                'title': title,
                'icon': icon,
                'meta': {
                    "pack": {
                        "description": f"{description}",
                        "pack_format": number
                    }
                }
            }
            self.newPack(packData)
            self.edit_pack_info.setEnabled(self.packConrols.packCreated)

    ## Wrappers ##

    def newPack(self, packData=False):
        self.packConrols.newPack(packData)
        self.paintingEditor.newPack()

    def setButtonEnabled(self, value):
        listFull = self.packConrols.updateButtonEnabled()
        self.save_draft_as_action.setEnabled(listFull)
        self.save_draft_action.setEnabled(listFull)
        self.batch_edit_action.setEnabled(listFull)
        self.packConrols.add_button.setEnabled(value)
        self.paintingEditor.setButtonEnabled(value)
        self.edit_pack_info.setEnabled(self.packConrols.packCreated)
        return

    def loadFromFile(self, file=False):
        dialog = SaveChangesDialog(self,self.packConrols.changesSaved)
        reply = dialog.getReply()
        if reply == QMessageBox.Yes:
            self.saveExisting()
            pass
        elif reply == QMessageBox.No:
            pass
        else:
            return
        directory = os.path.join(os.path.expanduser("~"), "Documents")
        if not file:
            file, _ = QFileDialog.getOpenFileName(self, 'Load Draft', directory, 'PaintingStudio Draft (*.pson *.json)')
        try:
            self.packConrols.openDraft(file)
        except Exception as e:
            traceback.print_exc()
            QMessageBox.warning(self, "Draft Load Error", f"An error occured when reading the draft's data:\n\n{e}")

    # =============================================================

    def generateImage(self, image=None, options=None, silentDraw=False):
        self.paintingEditor.generateImage(image, options, silentDraw)

    def notify(self, msg, interval=2000):
        self.paintingEditor.notify(msg, interval)

    def addPainting(self, data):
        self.paintingEditor.optionsPanel.addPainting(data)

    def removePainting(self, paintingName):
        self.paintingEditor.optionsPanel.removePainting(paintingName)

    def getCurrentImage(self, storage_type):
        return self.paintingEditor.getCurrentImage(storage_type)

    def setData(self, data={}):
        self.paintingEditor.setData(data)

    def setCurrentImage(self, file_path):
        return self.paintingEditor.setCurrentImage(file_path)

    # =============================================================

    def saveToFile(self):
        self.packConrols.saveDraft()

    def saveExisting(self):
        if self.save_draft_action.isEnabled():
            self.packConrols.saveDraft(self.packConrols.saveFile)

    def requestViewPortDraw(self):
        self.paintingEditor.requestViewPortDraw()

    def setCurrentData(self, paintingName, paintingMetaData):
        self.paintingEditor.setCurrentData(paintingName, paintingMetaData)

    def getCurrentImageData(self):
        return self.paintingEditor.getCurrentImageData()

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

def set_theme(app):
    desktop = ""
    try:
        qt_based = [
            "plasma"
        ]
        desktop = os.environ.get('DESKTOP_SESSION')
        if not any(sub in desktop for sub in qt_based):
            available_styles = QStyleFactory.keys()
            if "Adwaita-Dark" in available_styles:
                app.setStyle("Adwaita-Dark")
            else:
                desktop = ""
    except Exception as e:
        traceback.print_exc()
        print(f"Failed to get env: {e}")
        pass
    current_style = app.style().objectName()
    print(f"desktop detected as: '{desktop}'")
    if desktop == "" or current_style == "windowsvista":
        desktop = "windows"
        try:
            with open(ResourcePath("styles", "Adwaita-Dark.qss"), "r") as f:
                app.setStyleSheet(f.read())
        except:
            print("Failed to load darkmode")
            pass
    #print(f"Loaded Theme: {current_style} on {desktop}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    set_theme(app)
    window = PaintingStudio()
    #window.setObjectName("Frame")
    window.show()
    try:
        if len(sys.argv) > 1:
            print(sys.argv[1])
            window.loadFromFile(sys.argv[1])
        else:
            window.checkForUpdates()
            window.makeNewPack()
    except:
        window.makeNewPack()
        print("Draft too old or failed to parse")
    sys.exit(app.exec_())
