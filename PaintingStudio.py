import os
import json
import sys
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QComboBox, QLabel, QFrame, QHBoxLayout, QFileDialog
from io import BytesIO
from PIL import Image 
from PaintingGenerator import PaintingGenerator
from ResourcePackBuilder import ResourcePackBuilder


class PaintingStudio(QWidget):
     
    def __init__(self):
        super().__init__()
        with open('paintings.json', 'r') as file:
            self.paintings = json.load(file)
        self.used_paintings = []
        self.newPack()
        
        # generated stuff
        
        self.setWindowTitle("Drag and Drop Image Example")
        self.setGeometry(100, 100, 600, 400)

        # Set up the layout
        layout = QVBoxLayout(self)
        
        # Create the drop zone (a frame to indicate where the user should drop files)
        self.drop_zone = QFrame(self)
        self.drop_zone.setFrameShape(QFrame.StyledPanel)
        self.drop_zone.setStyleSheet("background-color: lightgray;")
        self.drop_zone.setAcceptDrops(True)

        # Create the combo boxes
        self.combo_box_1 = QComboBox(self)
        self.combo_box_2 = QComboBox(self)
        self.combo_box_1.addItem("Option 1")
        self.combo_box_1.addItem("Option 2")
        self.combo_box_2.addItem("Option 1")
        self.combo_box_2.addItem("Option 2")

        # Add the widgets to the layout
        layout.addWidget(self.drop_zone)
        layout.addWidget(self.combo_box_1)
        layout.addWidget(self.combo_box_2)

        # Label to show the dragged image file name
        self.image_label = QLabel("Dropped image will appear here", self)
        layout.addWidget(self.image_label)
    
    def newPack(self):
        mcMeta = { 
            "pack": {
                "description": "NSFW Furry Paintings!",
                "pack_format": 42
            }
        }
        self.pack_builder = ResourcePackBuilder("NSFW_furry_paintings", "../pack.png" , mcMeta)
        self.painting_maker = PaintingGenerator()
    
    def writeImage(self, paintingName, painting):
        self.used_paintings += [paintingName] 
        image_bytes = BytesIO()
        painting.save(image_bytes, format='PNG')
        image_bytes.seek(0)
        self.pack_builder.addFile(f'assets/minecraft/textures/painting/{paintingName}.png', image_bytes.read())
        
    def savePack(self):
        self.pack_builder.writePack()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        # Get the dropped file path
        file_path = event.mimeData().urls()[0].toLocalFile()
        self.handle_dropped_image(file_path)

    def handle_dropped_image(self, file_path):
        try:
            # Open the image using Pillow
            pil_image = Image.open(file_path)

            # Display the image using a QLabel
            pixmap = QPixmap(file_path)
            self.image_label.setPixmap(pixmap.scaled(200, 200, Qt.KeepAspectRatio))

            # Show the details about the Pillow image object
            self.image_label.setText(f"Image dropped: {file_path}\n"
                                     f"Image size: {pil_image.size}\n"
                                     f"Image format: {pil_image.format}")

        except Exception as e:
            self.image_label.setText(f"Failed to open image: {str(e)}")

    def setAcceptDrops(self, value: bool):
        super().setAcceptDrops(value)
        self.drop_zone.setAcceptDrops(value)

    def testData():
        path = "../input_nsfw/backyard.png"
        
        for types in self.paintings['3x4']:
            if types not in self.used_paintings:
                print(types)
        
        art = Image.open(path)
        painting = self.painting_maker.makePaiting(4, self.paintings['3x4'][0], art)
        self.writeImage(self.paintings['3x4'][0], painting)

        for types in self.paintings['3x4']:
            if types not in self.used_paintings:
                print(types)

        self.savePack()
     
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PaintingStudio()
    window.show()
    sys.exit(app.exec_())
