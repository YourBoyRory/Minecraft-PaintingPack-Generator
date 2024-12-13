from PyQt5.QtCore import Qt, QUrl, QSize, QTimer, QStringListModel, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage, QIcon, QColor, QFont
from PyQt5.QtWidgets import QScrollArea, QSlider, QMainWindow, QMessageBox, QMenuBar, QDialog, QColorDialog, QFormLayout, QLineEdit, QMenu, QAction, QListWidgetItem, QListWidget, QTabWidget, QApplication, QWidget, QVBoxLayout, QComboBox, QLabel, QFrame, QHBoxLayout, QFileDialog, QSizePolicy, QSpinBox, QPushButton
from PyQt5.QtWidgets import QApplication, QStyleFactory, QProgressBar
from FrameDialog import LoadingDialog
from ResourcePackBuilder import ResourcePackBuilder
from io import BytesIO
import json
import sys
import os

class PackControls(QWidget):

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        
        self.used_paintings = {}
        PackConrols_layout = QVBoxLayout()

        # Pack Info
        packinfo_layout = QHBoxLayout()
        self.packIcon_label = QLabel()
        self.packIcon_label.setFixedSize(110,100)
        self.packTitle_label = QLabel()
        self.packTitle_label.setWordWrap(True)
        packinfo_layout.addWidget(self.packIcon_label)
        packinfo_layout.addWidget(self.packTitle_label)
        PackConrols_layout.addLayout(packinfo_layout)

        # Painting List
        self.listwidget = QListWidget(self)
        self.listwidget.setSelectionMode(3)
        self.listwidget.setContextMenuPolicy(3)
        self.listwidget.customContextMenuRequested.connect(self.show_context_menu)
        font = QFont()
        font.setPointSize(9)
        self.listwidget.setFont(font)
        PackConrols_layout.addWidget(self.listwidget)

        # Control Buttons
        button_layout = QHBoxLayout()
        self.add_button = QPushButton("Add Painting", self)
        self.add_button.clicked.connect(self.writeImage)
        self.export_button = QPushButton("Export Pack", self)
        self.export_button.clicked.connect(self.exportPack)
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.export_button)
        PackConrols_layout.addLayout(button_layout)
        self.setLayout(PackConrols_layout)

    def updateButtonEnabled(self):
        if self.listwidget.count() == 0:
            self.export_button.setEnabled(False)
            return False
        else:
            self.export_button.setEnabled(True)
            return True

    def show_context_menu(self, pos):
        global_pos = self.listwidget.mapToGlobal(pos)
        item = self.listwidget.itemAt(pos)
        context_menu = QMenu(self)
        delete_action = QAction("Delete Painting", self)
        delete_action.triggered.connect(lambda: self.removeImage(item))
        edit_action = QAction("Edit Painting", self)
        edit_action.triggered.connect(lambda: self.editImage(item))
        context_menu.addAction(delete_action)
        context_menu.addAction(edit_action)
        if item == None:
            delete_action.setEnabled(False)
            edit_action.setEnabled(False)
        context_menu.exec_(global_pos)

    def setPackInfo(self, title, packMeta, icon):
            self.packName = title
            number = packMeta['pack']['pack_format']
            description = packMeta['pack']['description']
            self.pack_builder = ResourcePackBuilder(packMeta)
            if icon != None:
                pil_image = Image.open(icon).convert('RGB')
                pil_image_resized = pil_image.resize((64,64))
                image_bytes = BytesIO()
                pil_image_resized.save(image_bytes, format='PNG')
                image_bytes.seek(0)
                self.pack_builder.addFile("assets/pack.png", image_bytes.read())
                data = pil_image_resized.tobytes("raw", "RGB")
                qim = QImage(data, pil_image_resized.width, pil_image_resized.height, QImage.Format_RGB888)
                pixmap = QPixmap(QPixmap.fromImage(qim))
            else:
                print("No Image Provided")
                pixmap = QPixmap(self.resource_path("pack.png"))
            self.packIcon_label.setPixmap(pixmap.scaled(QSize(100, 100), aspectRatioMode=1))
            self.packTitle_label.setText(f"{title}\nFormat: {number}\n\n{description}")
            self.listwidget.clear()

    def removeImage(self, item):
        try:
            name = item.text().split()[0].lower()
            size = item.text().split()[1].replace("(", "").replace(")", "")
        except Exception as e:
            print(f"Failed to remove image: {str(e)}")
            return
        self.pack_builder.delFile(f"assets/minecraft/textures/painting/{name}.png")
        self.listwidget.takeItem(self.listwidget.row(item))
        self.used_paintings.pop(name, None)
        if self.parent.size_combo_box.findText(size) == -1:
            self.parent.size_combo_box.addItem(size)
        self.parent.updateComboBox()
        if self.listwidget.count() == 0:
            self.export_button.setEnabled(False)
            self.parent.save_draft_action.setEnabled(False)
        else:
            self.export_button.setEnabled(True)
            self.parent.save_draft_action.setEnabled(True)

    def editImage(self, item):
        try:
            name = item.text().split()[0].lower()
            size = item.text().split()[1].replace("(", "").replace(")", "")
        except Exception as e:
            print(f"Failed to edit image: {str(e)}")
            return
        self.pack_builder.delFile(f"assets/minecraft/textures/painting/{name}.png")
        self.listwidget.takeItem(self.listwidget.row(item))
        if self.parent.size_combo_box.findText(size) == -1:
            self.parent.size_combo_box.addItem(size)
        if self.listwidget.count() == 0:
            self.export_button.setEnabled(False)
            self.parent.save_draft_action.setEnabled(False)
        else:
            self.export_button.setEnabled(True)
        paintingMetaData = self.used_paintings[name]
        self.used_paintings.pop(name, None)
        self.parent.setCurrentImage(paintingMetaData['file_path'])
        self.parent.setCurrentData(name, paintingMetaData)


    def writeImage(self):
        self.parent.lock = True
        imageData, paintingName, painting = self.parent.getCurrentImageData()

        detail = imageData[paintingName]['detail']
        frameName = imageData[paintingName]['frameName']
        size = imageData[paintingName]['size']
        scale_method = imageData[paintingName]['scale_method']
        backgroundColor = imageData[paintingName]['background_color']
        #imageData[paintingName]['frame_index'] = self.frame_combo_box.currentIndex()


        image_bytes = BytesIO()
        painting.save(image_bytes, format='PNG')
        image_bytes.seek(0)
        self.pack_builder.addFile(f'assets/minecraft/textures/painting/{paintingName}.png', image_bytes.read())
        item1 = QListWidgetItem(f"{paintingName.title()} ({size})\nFrame: {frameName.title()}\n\nDetail: {detail}x\nScale Method: {scale_method}\nBackground Color: {backgroundColor}")
        item1.setIcon(QIcon(self.parent.image_label.pixmap()))  # Set QPixmap as an icon
        self.listwidget.addItem(item1)
        self.listwidget.setIconSize(QSize(100, 100))
        self.used_paintings[paintingName] = imageData[paintingName]
        self.parent.updateComboBox()
        self.parent.setButtonEnabled(False)
        self.parent.image_label.clear()
        self.parent.image_label.setText("Drop Next image here")
        self.parent.path_label.setText("")
        self.parent.view_size = 400
        self.parent.image_label.setFixedSize(self.parent.view_size, self.parent.view_size)
        self.parent.handle_dropped_image()

    def exportPack(self):
        options = QFileDialog.Options()
        file, _ = QFileDialog.getSaveFileName(self, "Save Resource Pack", f"{self.packName}.zip", "MC Resource Pack (*.zip);;All Files (*)", options=options)
        if file:
            self.pack_builder.writePack(file)
            QMessageBox.information(self, "Pack Saved", f"Resource Pack saved to\n{file}")

    def loadDraft(self):
        dialog = LoadingDialog(self)
        file_name, _ = QFileDialog.getOpenFileName(self, 'Load Draft', '', 'PaintingStudio Draft (*.json)')
        if file_name:
            self.listwidget.clear()
            self.used_paintings = {}
            self.parent.updateComboBox()
            with open(file_name) as f:
                loaded_paintings = json.load(f)
            i=1
            dialog.show_loading(len(loaded_paintings))
            for paintingName in loaded_paintings:
                self.used_paintings[paintingName] = loaded_paintings[paintingName]
                paintingMetaData = loaded_paintings[paintingName]
                self.used_paintings.pop(paintingName, None)
                self.parent.setCurrentImage(paintingMetaData['file_path'])
                self.parent.setCurrentData(paintingName, paintingMetaData)
                self.writeImage()
                dialog.update_progress_signal.emit(i)
                QApplication.processEvents()
                i+=1
            dialog.close_dialog()

    def saveDraft(self, file=None):
        options = QFileDialog.Options()
        if file == None:
            file, _ = QFileDialog.getSaveFileName(self, "Save Draft", f"{self.packName}.json", "PaintingStudio Draft (*.json)", options=options)
        if file:
            with open(file, "w") as fp:
                json.dump(self.used_paintings, fp)
            QMessageBox.information(self, "Draft Saved", f"Draft saved to\n{file}")

    def resource_path(self, file):
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(__file__)
        return os.path.join(base_path, 'assets', file)
