import os
import json
import sys
from PyQt5.QtCore import Qt, QSize, QStringListModel
from PyQt5.QtGui import QPixmap, QImage, QIcon, QColor
from PyQt5.QtWidgets import QMessageBox, QColorDialog, QMenu, QAction, QListWidgetItem, QListWidget, QTabWidget, QApplication, QWidget, QVBoxLayout, QComboBox, QLabel, QFrame, QHBoxLayout, QFileDialog, QSizePolicy, QSpinBox, QPushButton
from io import BytesIO
from PIL import Image 
from PaintingGenerator import PaintingGenerator
from ResourcePackBuilder import ResourcePackBuilder


class PaintingStudio(QWidget):
     
    def __init__(self):
        super().__init__()
        with open('paintings.json', 'r') as file:
            self.paintings = json.load(file)
        self.newPack()
        self.used_paintings = []
        self.lock = True
        self.updating = False
        self.backgroundColor = "#000000"
        
        # generated stuff
        self.tab_widget = QTabWidget(self)
        self.setWindowTitle("Minecraft Painting Studio")
        self.setGeometry(100, 100, 800, 800)

        # Set up the layout
        layout = QVBoxLayout(self)
        
        tab1 = QWidget()
        tab1_layout = QVBoxLayout()
        tab1.setLayout(tab1_layout)
        
        tab2 = QWidget()
        tab2_layout = QVBoxLayout()
        self.listwidget = QListWidget(self)
        #self.listwidget.clicked.connect(self.list_clicked)
        self.listwidget.setSelectionMode(3)
        #self.listwidget.setMouseTracking(True)
        self.listwidget.setIconSize(QSize(50, 50))
        #self.listwidget.setMaximumWidth(500)
        #self.listwidget.setMinimumWidth(300)
        #self.listwidget.setMinimumHeight(550)
        #self.listwidget.setStyleSheet(style)
        self.listwidget.setContextMenuPolicy(3)
        self.listwidget.customContextMenuRequested.connect(self.show_context_menu)
        tab2_layout.addWidget(self.listwidget)
        tab2.setLayout(tab2_layout)
        
        button_layout = QHBoxLayout()
        self.add_button = QPushButton("Add Painting", self)
        self.add_button.clicked.connect(self.writeImage)
        self.export_button = QPushButton("Save Pack", self)
        self.export_button.clicked.connect(self.savePack)
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.export_button)
        
        # Create the combo boxes
        lable_width = 100
        detail_layout = QHBoxLayout()
        self.detail_spin_box = QSpinBox(self)
        self.detail_spin_box.setRange(1, 16)  # Set the valid range (1 to 100)
        self.detail_spin_box.setValue(1)  # Set the initial value
        self.detail_spin_box.valueChanged.connect(self.updateImage)
        detail_label = QLabel('Detail: ')
        detail_label.setMaximumWidth(lable_width)
        detail_layout.addWidget(detail_label)
        detail_layout.addWidget(self.detail_spin_box)
       
        scale_layout = QHBoxLayout()
        self.scale_combo_box = QComboBox(self)
        scale_label = QLabel('Scale Method: ')
        scale_label.setMaximumWidth(lable_width)
        scale_layout.addWidget(scale_label)
        self.scale_combo_box.addItems(["Stretch", "Fit", "Crop"])
        self.color_button = QPushButton('Choose Backgroud Color', self)
        self.color_button.clicked.connect(self.showColorDialog)
        scale_layout.addWidget(self.scale_combo_box)
        scale_layout.addWidget(self.color_button)
        
        size_layout = QHBoxLayout()
        self.size_combo_box = QComboBox(self)
        size_label = QLabel('Painting Size: ')
        size_label.setMaximumWidth(lable_width)
        size_layout.addWidget(size_label)
        size_layout.addWidget(self.size_combo_box)
        
        
        painting_layout = QHBoxLayout()
        self.painting_combo_box = QComboBox(self)
        painting_label = QLabel('Painting: ')
        painting_label.setMaximumWidth(lable_width)
        painting_layout.addWidget(painting_label)
        painting_layout.addWidget(self.painting_combo_box)
        self.frame_combo_box = QComboBox(self)
        frame_label = QLabel('Frame: ')
        frame_label.setMaximumWidth(lable_width//2)
        painting_layout.addWidget(frame_label)
        painting_layout.addWidget(self.frame_combo_box)
        
        self.setButtonEnabled(False)
        
        for key in self.paintings:
            self.size_combo_box.addItem(key)
        self.updateComboBox()
        self.size_combo_box.currentIndexChanged.connect(self.updateComboBox)
        self.painting_combo_box.currentIndexChanged.connect(self.updateFrameComboBox)
        self.scale_combo_box.currentIndexChanged.connect(self.updateImage)
        self.frame_combo_box.currentIndexChanged.connect(self.updateImage)

        # Label to show the dragged image file name and details
        self.image_label = QLabel("Drop image here to customize your painting", self)
        
        # Ensure the label scales its size to fit the image
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Add the widgets to the layout
        tab1_layout.addLayout(detail_layout)
        tab1_layout.addLayout(size_layout)
        tab1_layout.addLayout(scale_layout)
        tab1_layout.addLayout(painting_layout)
        tab1_layout.addWidget(self.image_label)
        tab1_layout.addLayout(button_layout)
        
        self.tab_widget.addTab(tab1, "Painting Studio")
        self.tab_widget.addTab(tab2, "Added Paintings")
        
        layout.addWidget(self.tab_widget)
        self.setLayout(layout)

        # Set the whole window to accept drops
        self.setAcceptDrops(True)
    
    def newPack(self):
        self.packName = "NSFW_furry_paintings"
        self.packIcon = "../pack.png"
        self.packMeta = { 
            "pack": {
                "description": "NSFW Furry Paintings!",
                "pack_format": 42
            }
        }
        self.pack_builder = ResourcePackBuilder(self.packName , self.packIcon , self.packMeta)
        self.painting_maker = PaintingGenerator()
    
    def setButtonEnabled(self, value):
        self.detail_spin_box.setEnabled(value)
        self.size_combo_box.setEnabled(value)
        self.painting_combo_box.setEnabled(value)
        self.frame_combo_box.setEnabled(value)
        self.scale_combo_box.setEnabled(value)
        self.add_button.setEnabled(value)
        self.color_button.setEnabled(value)
        if self.listwidget.count() == 0:
            self.export_button.setEnabled(False)
        else:
            self.export_button.setEnabled(True)

    def show_context_menu(self, pos):
        global_pos = self.listwidget.mapToGlobal(pos)
        item = self.listwidget.itemAt(pos)
        context_menu = QMenu(self)
        delete_action = QAction("Delete Item", self)
        delete_action.triggered.connect(lambda: self.removeImage(item))
        context_menu.addAction(delete_action)
        context_menu.exec_(global_pos)

    def removeImage(self, item):
        self.pack_builder.delFile(f"assets/minecraft/textures/painting/{item.text()}.png")
        self.listwidget.takeItem(self.listwidget.row(item))
        self.updateUsedPaintings()
        #self.updateComboBox()
    
    def writeImage(self):
        self.lock = True
        paintingName = self.painting_combo_box.currentText() 
        image_bytes = BytesIO()
        self.painting.save(image_bytes, format='PNG')
        image_bytes.seek(0)
        self.pack_builder.addFile(f'assets/minecraft/textures/painting/{paintingName}.png', image_bytes.read())
        item1 = QListWidgetItem(paintingName)
        item1.setIcon(QIcon(self.image_label.pixmap()))  # Set QPixmap as an icon
        self.listwidget.addItem(item1)
        self.updateUsedPaintings()
        self.updateComboBox()
        self.setButtonEnabled(False)
        self.image_label.clear()
        self.image_label.setText("Drop Next image here")
     
    def updateUsedPaintings(self):
        items = []
        for i in range(self.listwidget.count()):
            item = self.listwidget.item(i)
            items.append(item.text())
        self.used_paintings = items
        
    def savePack(self):
        options = QFileDialog.Options()
        file, _ = QFileDialog.getSaveFileName(self, "Save File", self.packName, "MC Resource Pack (*.zip);;All Files (*)", options=options)
        if file:
            self.pack_builder.writePack(file)
            QMessageBox.information(self, "Pack Saved", f"Resource Pack saved to\n{file}")

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        # Get the dropped file path
        file_path = event.mimeData().urls()[0].toLocalFile()
        self.handle_dropped_image(file_path)

    def showColorDialog(self):
        # Open the QColorDialog
        color = QColorDialog.getColor(QColor(self.backgroundColor))

        if color.isValid():
            # Update the label with the chosen color
            self.backgroundColor = color.name()
        self.updateImage()

    def handle_dropped_image(self, file_path):
        try:
            self.lock = False
            self.file_path = file_path
            self.updateImage()
            self.setButtonEnabled(True)
        except Exception as e:
            self.lock = True
            self.image_label.setText(f"Failed to open image: {str(e)}")

    def pushImageUpdate(self):
        if self.lock == False:
            # Open the image using Pillow
            detail = self.detail_spin_box.value()
            scale_method = self.scale_combo_box.currentText()
            size = self.size_combo_box.currentText()
            painting = self.painting_combo_box.currentIndex()
            frame = self.frame_combo_box.currentIndex()
            art = Image.open(self.file_path)
            self.painting = self.painting_maker.makePaiting(detail, scale_method, self.backgroundColor, self.paintings[size][frame], art)
                    
            # Convert the image to QPixmap for display
            pil_image = self.painting.convert("RGB")
            data = pil_image.tobytes("raw", "RGB")
            qim = QImage(data, pil_image.width, pil_image.height, QImage.Format_RGB888)
            pixmap = QPixmap(QPixmap.fromImage(qim))
            # Display the image at full size in the label
            self.image_label.setPixmap(pixmap.scaled(QSize(600, 400), aspectRatioMode=1))
        else:
            print("WARN: A push to the image view was preformed while it was locked!")

    def updateImage(self):
        if self.updating == True:
            #print("WARN: blocked update, update in progress.")
            return
        if self.lock == True:
            print("WARN: A push to the image view was preformed while it was locked!")
            return
        self.pushImageUpdate()
        
    def updateFrameComboBox(self):
        self.frame_combo_box.setCurrentText(self.painting_combo_box.currentText())
        
    def updateComboBox(self):
        self.updating = True
        size = self.size_combo_box.currentText()
        self.frame_combo_box.clear()
        self.painting_combo_box.clear()
        for types in self.paintings[size]:
            self.frame_combo_box.addItem(types)
            if types not in self.used_paintings:
                self.painting_combo_box.addItem(types)
        if self.painting_combo_box.currentText() == "":
            self.size_combo_box.removeItem(self.size_combo_box.currentIndex())
        try:
            self.pushImageUpdate()
        except Exception as e:
            print(f"Failed to open image: {str(e)}")
        self.updating = False
     
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PaintingStudio()
    window.show()
    sys.exit(app.exec_())
