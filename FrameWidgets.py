from PyQt5.QtCore import Qt, QUrl, QSize, QTimer, QStringListModel, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage, QIcon, QColor, QFont
from PyQt5.QtWidgets import QScrollArea, QSlider, QMainWindow, QMessageBox, QMenuBar, QDialog, QColorDialog, QFormLayout, QLineEdit, QMenu, QAction, QListWidgetItem, QListWidget, QTabWidget, QApplication, QWidget, QVBoxLayout, QComboBox, QLabel, QFrame, QHBoxLayout, QFileDialog, QSizePolicy, QSpinBox, QPushButton
from PyQt5.QtWidgets import QApplication, QStyleFactory, QProgressBar
from ResourcePackBuilder import ResourcePackBuilder
from io import BytesIO
import sys
import os

class PackControls(QWidget):

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

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
        self.export_button = QPushButton("Save Pack", self)
        self.export_button.clicked.connect(self.parent.savePack)
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.export_button)
        PackConrols_layout.addLayout(button_layout)
        self.setLayout(PackConrols_layout)

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
            self.parent.pack_builder.delFile(f"assets/minecraft/textures/painting/{name}.png")
            self.listwidget.takeItem(self.listwidget.row(item))
            self.used_paintings.pop(name, None)
            if self.size_combo_box.findText(size) == -1:
                self.size_combo_box.addItem(size)
            self.updateComboBox()
            if self.listwidget.count() == 0:
                self.export_button.setEnabled(False)
                self.save_draft_action.setEnabled(False)
            else:
                self.export_button.setEnabled(True)
                self.save_draft_action.setEnabled(True)
        except Exception as e:
            print(f"Failed to remove image: {str(e)}")

    def writeImage(self):
        self.parent.lock = True
        imageData, paintingName, painting = self.parent.getCurrentImageData()

        detail = imageData[paintingName]['detail']
        frameName = imageData[paintingName]['frameName']
        size = imageData[paintingName]['size']
        scale_method = imageData[paintingName]['scale_method']
        backgroundColor = imageData[paintingName]['backgroun_color']
        #imageData[paintingName]['frame_index'] = self.frame_combo_box.currentIndex()


        image_bytes = BytesIO()
        painting.save(image_bytes, format='PNG')
        image_bytes.seek(0)
        self.pack_builder.addFile(f'assets/minecraft/textures/painting/{paintingName}.png', image_bytes.read())
        item1 = QListWidgetItem(f"{paintingName.title()} ({size})\nFrame: {frameName.title()}\n\nDetail: {detail}x\nScale Method: {scale_method}\nBackground Color: {backgroundColor}")
        item1.setIcon(QIcon(self.parent.image_label.pixmap()))  # Set QPixmap as an icon
        self.listwidget.addItem(item1)
        self.listwidget.setIconSize(QSize(100, 100))
        self.parent.used_paintings[paintingName] = imageData
        self.parent.updateComboBox()
        self.parent.setButtonEnabled(False)
        self.parent.image_label.clear()
        self.parent.image_label.setText("Drop Next image here")
        self.parent.path_label.setText("")
        self.parent.view_size = 400
        self.parent.image_label.setFixedSize(self.parent.view_size, self.parent.view_size)
        self.parent.handle_dropped_image()

    def resource_path(self, file):
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(__file__)
        return os.path.join(base_path, 'assets', file)
