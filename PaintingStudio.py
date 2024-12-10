import os
import json
import sys
from pathlib import Path
from PyQt5.QtCore import Qt, QSize, QStringListModel
from PyQt5.QtGui import QPixmap, QImage, QIcon, QColor, QFont
from PyQt5.QtWidgets import QMessageBox, QMenuBar, QDialog, QColorDialog, QFormLayout, QLineEdit, QMenu, QAction, QListWidgetItem, QListWidget, QTabWidget, QApplication, QWidget, QVBoxLayout, QComboBox, QLabel, QFrame, QHBoxLayout, QFileDialog, QSizePolicy, QSpinBox, QPushButton
from io import BytesIO
from PIL import Image 
from PaintingGenerator import PaintingGenerator
from ResourcePackBuilder import ResourcePackBuilder

class InputDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.icon = None
        self.setWindowTitle("Create New Pack")
        
        # Create form layout
        layout = QFormLayout()
        
        # Create input fields
        self.title_input = QLineEdit("PaintingPack")
        self.description_input = QLineEdit("My Painting Pack")
        self.number_input = QSpinBox()
        self.number_input.setValue(42)
        self.number_input.setRange(0, 100)  # Set the range for the spinner
        self.iconButton = QPushButton("Set Pack Icon")
        self.iconButton.clicked.connect(self.setIcon)
        
        # Add fields to the layout
        layout.addRow("Title:", self.title_input)
        layout.addRow("Description:", self.description_input)
        layout.addRow("Pack Format:", self.number_input)
        layout.addRow(self.iconButton)
        
        # Create Ok and Cancel buttons
        self.ok_button = QPushButton("Ok")
        self.cancel_button = QPushButton("Cancel")
        
        # Add buttons to the layout
        layout.addRow(self.ok_button, self.cancel_button)
        
        # Set dialog layout
        self.setLayout(layout)
        
        # Connect buttons to functions
        self.ok_button.clicked.connect(self.on_ok_button_clicked)
        self.cancel_button.clicked.connect(self.reject)

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

class PaintingStudio(QWidget):
     
    def __init__(self):
        super().__init__()
        with open('paintings.json', 'r') as file:
            self.paintings = json.load(file)
        self.used_paintings = []
        self.file_path_stack = []
        self.lock = True
        self.updating = False
        self.packCreated = False 
        self.backgroundColor = "#000000"
        
        # generated stuff
        self.tab_widget = QTabWidget(self)
        self.setWindowTitle("Minecraft Painting Studio")
        self.setGeometry(100, 100, 800, 800)

        menubar = QMenuBar()
        file_menu = menubar.addMenu('File')
        
        new_pack_action = QAction('New Pack', self)
        new_pack_action.triggered.connect(self.newPack)
        
        file_menu.addAction(new_pack_action)
        
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
        font = QFont()
        font.setPointSize(18)
        self.listwidget.setFont(font)
        tab2_layout.addWidget(self.listwidget)
        packinfo_layout = QHBoxLayout()
        self.packIcon_label = QLabel()
        self.packIcon_label.setFixedSize(110,100)
        self.packTitle_label = QLabel()
        packinfo_layout.addWidget(self.packIcon_label)
        packinfo_layout.addWidget(self.packTitle_label)
        tab2_layout.addLayout(packinfo_layout)
        tab2.setLayout(tab2_layout)
        
        
        button_layout = QHBoxLayout()
        self.add_button = QPushButton("Add Painting", self)
        self.add_button.clicked.connect(self.writeImage)
        self.export_button = QPushButton("Save Pack", self)
        self.export_button.clicked.connect(self.savePack)
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.export_button)
        
        # Create the combo boxes
        lable_width = 120
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
        self.scaleOptions = ["Stretch", "Fit", "Crop"]
        self.scale_combo_box.addItems(self.scaleOptions)
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
        self.path_label = QLabel("", self)
        
        # Ensure the label scales its size to fit the image
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Add the widgets to the layout
        tab1_layout.addLayout(detail_layout)
        tab1_layout.addLayout(size_layout)
        tab1_layout.addLayout(scale_layout)
        tab1_layout.addLayout(painting_layout)
        tab1_layout.addWidget(self.image_label)
        tab1_layout.addWidget(self.path_label)
        tab1_layout.addLayout(button_layout)
        
        self.tab_widget.addTab(tab1, "Painting Studio")
        self.tab_widget.addTab(tab2, "Added Paintings")
        
        layout.addWidget(menubar)
        layout.addWidget(self.tab_widget)
        self.setLayout(layout)

        # Set the whole window to accept drops
        self.setAcceptDrops(True)
    
    def newPack(self):
        # Create and show the input dialog
        dialog = InputDialog(self)
        
        # Check if the dialog was accepted
        if dialog.exec_() == QDialog.Accepted:
            title, description, number, icon = dialog.get_data()
            self.painting_maker = PaintingGenerator()   
            self.packCreated = True
            self.packName = title
            self.packMeta = { 
                "pack": {
                    "description": f"{description}",
                    "pack_format": number
                }
            }
            self.pack_builder = ResourcePackBuilder(self.packMeta)
            if icon != None:
                pil_image = Image.open(icon).convert('RGB')
                pil_image_resized = pil_image.resize((64,64))
                image_bytes = BytesIO()
                pil_image_resized.save(image_bytes, format='PNG')
                image_bytes.seek(0)
                self.pack_builder.addFile("pack.png", image_bytes.read())
                data = pil_image_resized.tobytes("raw", "RGB")
                qim = QImage(data, pil_image_resized.width, pil_image_resized.height, QImage.Format_RGB888)
                pixmap = QPixmap(QPixmap.fromImage(qim))
            else:
                pixmap = QPixmap("./assets/pack.png")
            self.packIcon_label.setPixmap(pixmap.scaled(QSize(100, 100), aspectRatioMode=1))
            self.packTitle_label.setText(f"{title}\nFormat: {number}\n\n{description}")
            
            
            #print(self.pack_builder.packData)
            self.listwidget.clear()
            self.used_paintings = []
            self.updateComboBox()
    
    def setButtonEnabled(self, value):
        if self.listwidget.count() == 0:
            self.export_button.setEnabled(False)
        else:
            self.export_button.setEnabled(True)
        self.add_button.setEnabled(value)
        return
        self.detail_spin_box.setEnabled(value)
        self.size_combo_box.setEnabled(value)
        self.painting_combo_box.setEnabled(value)
        self.frame_combo_box.setEnabled(value)
        self.scale_combo_box.setEnabled(value)
        
        self.color_button.setEnabled(value)

    def show_context_menu(self, pos):
        global_pos = self.listwidget.mapToGlobal(pos)
        item = self.listwidget.itemAt(pos)
        context_menu = QMenu(self)
        delete_action = QAction("Delete Item", self)
        delete_action.triggered.connect(lambda: self.removeImage(item))
        context_menu.addAction(delete_action)
        context_menu.exec_(global_pos)

    def removeImage(self, item):
        name = item.text().split()
        self.pack_builder.delFile(f"assets/minecraft/textures/painting/{name[0].lower()}.png")
        self.listwidget.takeItem(self.listwidget.row(item))
        self.used_paintings.remove(name[0].lower())
        #self.updateComboBox()
        if self.listwidget.count() == 0:
            self.export_button.setEnabled(False)
        else:
            self.export_button.setEnabled(True)
    
    def writeImage(self):
        self.lock = True
        
        paintingName = self.painting_combo_box.currentText()
        detail = self.detail_spin_box.value()
        scale_method = self.scale_combo_box.currentText()
        size = self.size_combo_box.currentText()
        painting = self.painting_combo_box.currentIndex()
        frame = self.frame_combo_box.currentIndex()
        frameName = self.frame_combo_box.currentText()
        
        image_bytes = BytesIO()
        self.painting.save(image_bytes, format='PNG')
        image_bytes.seek(0)
        self.pack_builder.addFile(f'assets/minecraft/textures/painting/{paintingName}.png', image_bytes.read())
        item1 = QListWidgetItem(f"{paintingName.title()} ({size})\nFrame: {frameName.title()}\n\nDetail: {detail}x\nScale Method: {scale_method}\nBackground Color: {self.backgroundColor}")
        item1.setIcon(QIcon(self.image_label.pixmap()))  # Set QPixmap as an icon
        self.listwidget.addItem(item1)
        self.listwidget.setIconSize(QSize(200, 200))
        self.used_paintings += [paintingName]
        self.updateComboBox()
        self.setButtonEnabled(False)
        self.image_label.clear()
        self.image_label.setText("Drop Next image here")
        self.path_label.setText("")
        self.handle_dropped_image()
        
    def savePack(self):
        options = QFileDialog.Options()
        file, _ = QFileDialog.getSaveFileName(self, "Save Resource Pack", f"{self.packName}.zip", "MC Resource Pack (*.zip);;All Files (*)", options=options)
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
        if self.packCreated == True:
            for file in event.mimeData().urls():
                self.file_path_stack.append(file)
            self.handle_dropped_image()
        else:
            QMessageBox.information(self, "Pack not Created", f"Please create a pack before importing images.")

    def showColorDialog(self):
        # Open the QColorDialog
        color = QColorDialog.getColor(QColor(self.backgroundColor))

        if color.isValid():
            # Update the label with the chosen color
            self.backgroundColor = color.name()
        self.updateImage()

    def handle_dropped_image(self):
        if len(self.file_path_stack) > 0:
            try:
                file_path = self.file_path_stack.pop()
                self.lock = False
                self.file_path = file_path.toLocalFile()
                
                file_name = Path(self.file_path).name.split(".")[0].lower()
                self.autoSetComboBoxes(file_name)
                
                self.path_label.setText(f"{self.file_path}")
                self.updateImage()
                self.setButtonEnabled(True)
            except Exception as e:
                self.lock = True
                self.handle_dropped_image()
                self.image_label.setText(f"Failed to open image: {str(e)}")
        else:
            print("Tree Done.")

    def autoSetComboBoxes(self, filename):
        try:
            options = filename.split("-")
            print(options)
            paintingName = options[0]
            for size, painting_list in self.paintings.items():
                for painting in painting_list:
                    if painting == paintingName:
                        self.size_combo_box.setCurrentText(size)
                        break
            self.painting_combo_box.setCurrentText(paintingName)
            
            if len(options) > 1:
                for option in options:
                    if option.isdigit():
                        if int(option) in range(1,17):
                            self.detail_spin_box.setValue(int(option))
                    elif option.title() in self.scaleOptions:
                        self.scale_combo_box.setCurrentText(option.title())
                self.frame_combo_box.setCurrentText(options[1])
                
        except:
            print("WARN: Failed to parse auto values")
            pass
            
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
    window.newPack()
    sys.exit(app.exec_())
