from PyQt5.QtCore import Qt, QUrl, QSize, QTimer, QStringListModel, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage, QIcon, QColor, QFont
from PyQt5.QtWidgets import QScrollArea, QSlider, QMainWindow, QMessageBox, QMenuBar, QDialog, QColorDialog, QFormLayout, QLineEdit, QMenu, QAction, QListWidgetItem, QListWidget, QTabWidget, QApplication, QWidget, QVBoxLayout, QComboBox, QLabel, QFrame, QHBoxLayout, QFileDialog, QSizePolicy, QSpinBox, QPushButton
from PyQt5.QtWidgets import QApplication, QStyleFactory, QProgressBar
from FrameDialog import LoadingDialog
from PaintingGenerator import PaintingGenerator
from ResourcePackBuilder import ResourcePackBuilder
from pathlib import Path
from io import BytesIO
from PIL import Image
import json
import sys
import os

class PaintingEditor(QWidget):
    
    def __init__(self, parent):
        super().__init__(parent)
        
        # This is very OOP thus its ok and cool
        self.parent = parent
        self.packConrols = self.parent.packConrols
        
        init_silder_value = 500
        self.view_size = int(100 + (init_silder_value / 500) * 300)

        with open(self.resource_path('paintings.json'), 'r') as file:
            self.paintings = json.load(file)
        self.file_path_stack = []
        self.drawThread = QTimer(self)
        self.drawThread.timeout.connect(self.forceViewPortDraw)
        self.drawThread.setSingleShot(True)
        self.lock = True
        self.updating = False
        self.backgroundColor = "#000000"
        
        PaintingEditor_Layout = QVBoxLayout()
        combine_OptionsViewport = QHBoxLayout()
        """Options Pane"""
        PaintingOptions = QWidget()
        PaintingOptions_layout = QVBoxLayout()

        lable_width = 120
        detail_layout = QHBoxLayout()
        self.detail_spin_box = QSpinBox(self)
        self.detail_spin_box.setRange(1, 16)  # Set the valid range (1 to 100)
        self.detail_spin_box.setValue(1)  # Set the initial value
        self.detail_spin_box.valueChanged.connect(self.requestViewPortDraw)
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
        scale_layout.addWidget(self.scale_combo_box)
        color_button_layout = QHBoxLayout()
        self.color_button = QPushButton('Choose Backgroud Color', self)
        self.color_button.clicked.connect(self.showColorDialog)
        color_button_layout.addWidget(self.color_button)

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
        frame_layout = QHBoxLayout()
        self.frame_combo_box = QComboBox(self)
        frame_label = QLabel('Frame: ')
        frame_label.setMaximumWidth(lable_width//2)
        frame_layout.addWidget(frame_label)
        frame_layout.addWidget(self.frame_combo_box)

        for key in self.paintings:
            self.size_combo_box.addItem(key)
        self.updateComboBox()
        self.size_combo_box.currentIndexChanged.connect(self.updateComboBox)
        self.painting_combo_box.currentIndexChanged.connect(self.updateFrameComboBox)
        self.scale_combo_box.currentIndexChanged.connect(self.requestViewPortDraw)
        self.frame_combo_box.currentIndexChanged.connect(self.requestViewPortDraw)

        # Add Layouts
        PaintingOptions_layout.addWidget(QLabel("<br><b>Framing Options</b>"))
        PaintingOptions_layout.addLayout(detail_layout)
        PaintingOptions_layout.addLayout(scale_layout)
        PaintingOptions_layout.addLayout(color_button_layout)
        PaintingOptions_layout.addWidget(QLabel("<br><b>Painting Options</b>"))
        PaintingOptions_layout.addLayout(size_layout)
        PaintingOptions_layout.addLayout(painting_layout)
        PaintingOptions_layout.addLayout(frame_layout)
        PaintingOptions_layout.addStretch()
        PaintingOptions.setLayout(PaintingOptions_layout)
        combine_OptionsViewport.addWidget(PaintingOptions)
        PaintingOptions.setMinimumWidth(250)
        PaintingOptions.setMaximumWidth(350)

        """View Port"""
        ViewPort = QWidget()
        ViewPort_layout = QVBoxLayout()
        # Main View Port
        scroll_area = QScrollArea(self)
        self.image_label = QLabel("Drop image here to customize your painting", self)
        scroll_area.setWidget(self.image_label)
        scroll_area.setAlignment(Qt.AlignCenter)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setWordWrap(True)
        self.image_label.setFixedSize(self.view_size, self.view_size)
        #Add Layouts
        ViewPort_layout.addWidget(scroll_area)
        ViewPort.setLayout(ViewPort_layout)
        combine_OptionsViewport.addWidget(ViewPort)
        PaintingEditor_Layout.addLayout(combine_OptionsViewport)
        ViewPort.setMinimumWidth(600)


        """Tool Bar"""
        ToolBar = QWidget()
        ToolBar_layout = QVBoxLayout()
        # View Port Tools
        tools_layout = QHBoxLayout()
        self.path_label = QLabel(" ", self)
        self.path_label.setMinimumWidth(1)
        #self.path_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
        self.view_slider = QSlider(Qt.Horizontal)
        self.view_slider.setRange(0,1000)  # Set minimum value
        self.view_slider.setValue(init_silder_value)  # Set initial value
        self.view_slider.setTickPosition(QSlider.TicksBelow)
        self.view_slider.setTickInterval(125)
        self.view_slider.setFixedWidth(100)
        self.view_slider.setMaximumWidth(150)
        self.view_slider.valueChanged.connect(self.view_slider_changed)
        tools_layout.addWidget(self.path_label)
        tools_layout.addStretch()
        tools_layout.addWidget(self.view_slider)
        #Add Layouts
        ToolBar_layout.addLayout(tools_layout)
        ToolBar.setLayout(ToolBar_layout)
        PaintingEditor_Layout.addWidget(ToolBar)
        self.setLayout(PaintingEditor_Layout)

    def newPack(self):
        self.painting_maker = PaintingGenerator()
        self.size_combo_box.clear()
        for key in self.paintings:
            self.size_combo_box.addItem(key)
        self.updateComboBox()

    def reset(self):
        for key in self.paintings:
            self.size_combo_box.addItem(key)
        self.updateComboBox()
        self.parent.setButtonEnabled(False)
        self.image_label.clear()
        self.image_label.setText("Drop image here to customize your painting")
        self.path_label.setText("")
        self.view_size = 400
        self.image_label.setFixedSize(self.view_size, self.view_size)


    def view_slider_changed(self):
        self.requestViewPortDraw()

    def update_view_size(self, autoScale = False):
        value = self.view_slider.value()
        if value <= 500:
            # Bottom half (100 to 400)
            self.view_size = int(100 + (value / 500) * 300)
        else:
            # Top half (400 to 1600)
            self.view_size = int(400 + ((value - 500) / 500) * 1200)
        self.image_label.setFixedSize(self.view_size, self.view_size)

    def setButtonEnabled(self, value):
        self.view_slider.setEnabled(value)
        return

    def setCurrentImage(self, file_path):
        # Put loaded image on the file stack
        self.file_path_stack.append(QUrl(f'file://{file_path}'))
        self.init_stack_count = len(self.file_path_stack)
        # Process image
        self.getNextImage()

    def setCurrentData(self, paintingName, paintingMetaData):
        # Load Meta Data
        print(paintingMetaData)
        detail = paintingMetaData["detail"]
        frameName = paintingMetaData["frameName"]
        size = paintingMetaData["size"]
        scale_method = paintingMetaData["scale_method"]
        background_color = paintingMetaData["background_color"]
        file_path = paintingMetaData["file_path"]
        # Set Options
        if not self.updating:
            self.updating = True
            self.detail_spin_box.setValue(detail)
            self.backgroundColor = background_color
            self.scale_combo_box.setCurrentText(scale_method)
            self.size_combo_box.setCurrentText(size)
            self.painting_combo_box.setCurrentText(paintingName)
            self.frame_combo_box.setCurrentText(frameName)
            self.updating = False

    def getCurrentImageData(self):
        paintingName = self.painting_combo_box.currentText()
        imageData = {}
        imageData[paintingName] = {}
        imageData[paintingName]['detail']  = self.detail_spin_box.value()
        imageData[paintingName]['frameName'] = self.frame_combo_box.currentText()
        imageData[paintingName]['size'] = self.size_combo_box.currentText()
        imageData[paintingName]['scale_method'] = self.scale_combo_box.currentText()
        imageData[paintingName]['background_color'] = self.backgroundColor
        imageData[paintingName]['frame_index'] = self.frame_combo_box.currentIndex()
        imageData[paintingName]['file_path'] = self.art_path
        return imageData, paintingName, self.painting

    def getCurrentImage(self):
        return self.image_label.pixmap()

    def showColorDialog(self):
        # Open the QColorDialog
        color = QColorDialog.getColor(QColor(self.backgroundColor))

        if color.isValid():
            # Update the label with the chosen color
            self.backgroundColor = color.name()
        self.requestViewPortDraw()

    def getNextImage(self):
        if len(self.file_path_stack) > 0:
            #try:
                url = self.file_path_stack.pop()
                if url.toLocalFile() == "":
                    self.art_path = url.toString()
                    response = requests.get(self.art_path)
                    img_data = BytesIO(response.content)
                    self.art = Image.open(img_data)
                    print(response.status_code)
                else:
                    self.art_path = url.toLocalFile()
                    self.art = Image.open(self.art_path)

                file_name = Path(self.art_path).name.split(".")[0].lower()
                self.forceViewPortDraw()
                self.autoSetComboBoxes(file_name)
                curr = self.init_stack_count-len(self.file_path_stack)
                self.path_label.setText(f"File: [{curr}/{self.init_stack_count}] - {self.art_path}")
                self.parent.setButtonEnabled(True)
            #except Exception as e:
            #    self.getNextImage()
            #    self.image_label.setText(f"Failed to open image: {str(e)}")
        else:
            self.init_stack_count = 0
            #print("Stack is empty.")
            self.lock = True
            self.updateComboBox()
            self.parent.setButtonEnabled(False)
            self.image_label.clear()
            self.image_label.setText("Drop Next image here")
            self.path_label.setText("")
            self.view_size = 400
            self.image_label.setFixedSize(self.view_size, self.view_size)

    def requestViewPortDraw(self):
        if self.drawThread.isActive():
            #print("WARN: Time delta short. ViewPort Locked")
            return
        if self.updating == True:
            #print("WARN: blocked update, update in progress.")
            return
        if self.lock == True:
            #print("WARN: A push to the image view was preformed while it was locked!")
            return
        self.drawThread.start(16) # 16ms frame delta

    def forceViewPortDraw(self):
        #if self.updating == True or self.lock == True:
            #print("WARN: Locked before Delta timeout. Skipping frame.")
            #return
        #print("Redrawing Viewport.")

        #Setting up UI
        self.update_view_size()

        # Getting Options
        detail = self.detail_spin_box.value()
        scale_method = self.scale_combo_box.currentText()
        size = self.size_combo_box.currentText()
        painting = self.painting_combo_box.currentIndex()
        frame = self.frame_combo_box.currentIndex()
        if self.frame_combo_box.currentText() == "None":
            showFrame = False
            frameName = self.paintings[size][0]
        else:
            showFrame = True
            frameName = self.paintings[size][frame]
        self.painting = self.painting_maker.makePaiting(detail, scale_method, self.backgroundColor, frameName, showFrame, self.art)

        # Display the image in viewport
        pil_image = self.painting.convert("RGB")
        data = pil_image.tobytes("raw", "RGB")
        qim = QImage(data, pil_image.width, pil_image.height, QImage.Format_RGB888)
        pixmap = QPixmap(QPixmap.fromImage(qim))
        self.image_label.setPixmap(pixmap.scaled(QSize(self.view_size, self.view_size), aspectRatioMode=1))

    def autoSetComboBoxes(self, filename):
        try:
            if self.updating == True:
                return
            options = filename.split("-")
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


    def updateFrameComboBox(self):
        if self.frame_combo_box.currentText() != "None":
            self.frame_combo_box.setCurrentText(self.painting_combo_box.currentText())

    def updateComboBox(self):
        self.updating = True
        size = self.size_combo_box.currentText()
        self.frame_combo_box.clear()
        self.painting_combo_box.clear()
        if size == "":
            #print("No Paintings.")
            return
        for types in self.paintings[size]:
            self.frame_combo_box.addItem(types)
            if types not in self.packConrols.used_paintings:
                self.painting_combo_box.addItem(types)
        self.frame_combo_box.addItem("None")
        if self.painting_combo_box.currentText() == "":
            self.size_combo_box.removeItem(self.size_combo_box.currentIndex())
        self.updating = False
        try:
            self.requestViewPortDraw()
        except Exception as e:
            print(f"Failed to open image: {str(e)}")
        #self.updating = False

    def resource_path(self, file):
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(__file__)
        return os.path.join(base_path, 'assets', file)

class PackControls(QWidget):

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

        self.packCreated = False
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
        self.listwidget.customContextMenuRequested.connect(self.showContextMenu)
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
        self.setMinimumWidth(250)
        self.setMaximumWidth(350)

    def updateButtonEnabled(self):
        if self.listwidget.count() == 0:
            self.export_button.setEnabled(False)
            return False
        else:
            self.export_button.setEnabled(True)
            return True

    def showContextMenu(self, pos):
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

    def reset(self):
        self.used_paintings = {}
        number = self.packMeta['pack']['pack_format']
        description = self.packMeta['pack']['description']
        self.pack_builder = ResourcePackBuilder(self.packMeta)
        if self.icon != None:
            pil_image = Image.open(self.icon).convert('RGB')
            pil_image_resized = pil_image.resize((64,64))
            image_bytes = BytesIO()
            pil_image_resized.save(image_bytes, format='PNG')
            image_bytes.seek(0)
            self.pack_builder.addFile("assets/pack.png", image_bytes.read())
            data = pil_image_resized.tobytes("raw", "RGB")
            qim = QImage(data, pil_image_resized.width, pil_image_resized.height, QImage.Format_RGB888)
            pixmap = QPixmap(QPixmap.fromImage(qim))
        else:
            #print("No Image Provided")
            pixmap = QPixmap(self.resource_path("pack.png"))
        self.packIcon_label.setPixmap(pixmap.scaled(QSize(100, 100), aspectRatioMode=1))
        self.packTitle_label.setText(f"{self.packName}\nFormat: {number}\n\n{description}")
        self.listwidget.clear()

    def setPackInfo(self, title, packMeta, icon):
        self.packCreated = True
        self.packName = title
        self.packMeta = packMeta
        self.icon = icon
        self.reset()

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
        self.parent.addToComboBox(size)
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
        self.parent.addToComboBox(size)
        if self.listwidget.count() == 0:
            self.export_button.setEnabled(False)
            self.parent.save_draft_action.setEnabled(False)
        else:
            self.export_button.setEnabled(True)
        paintingMetaData = self.used_paintings[name]
        self.used_paintings.pop(name, None)
        self.parent.setCurrentImage(paintingMetaData['file_path'])
        self.parent.setCurrentData(name, paintingMetaData)
        self.parent.setLockStatus(False)


    def writeImage(self):
        #self.parent.lock = True # Lock UI

        # Get the image data
        imageData, paintingName, painting = self.parent.getCurrentImageData()
        detail = imageData[paintingName]['detail']
        frameName = imageData[paintingName]['frameName']
        size = imageData[paintingName]['size']
        scale_method = imageData[paintingName]['scale_method']
        backgroundColor = imageData[paintingName]['background_color']

        # Push image to pack
        image_bytes = BytesIO()
        painting.save(image_bytes, format='PNG')
        image_bytes.seek(0)
        self.pack_builder.addFile(f'assets/minecraft/textures/painting/{paintingName}.png', image_bytes.read())

        # Add to Lists
        item1 = QListWidgetItem(f"{paintingName.title()} ({size})\nFrame: {frameName.title()}\n\nDetail: {detail}x\nScale Method: {scale_method}\nBackground Color: {backgroundColor}")
        item1.setIcon(QIcon(self.parent.getCurrentImage()))  # Set QPixmap as an icon
        self.listwidget.addItem(item1)
        self.listwidget.setIconSize(QSize(100, 100))
        self.used_paintings[paintingName] = imageData[paintingName]

        # Reset UI
        self.parent.getNextImage()

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
            self.reset()
            self.parent.reset()
            with open(file_name) as f:
                loaded_paintings = json.load(f)
            i=1
            dialog.show_loading(len(loaded_paintings))
            self.lock = False
            for paintingName in loaded_paintings:
                self.used_paintings[paintingName] = loaded_paintings[paintingName]
                paintingMetaData = loaded_paintings[paintingName]
                self.used_paintings.pop(paintingName, None)
                self.parent.setCurrentData(paintingName, paintingMetaData)
                self.parent.setCurrentImage(paintingMetaData['file_path'])
                self.parent.setCurrentData(paintingName, paintingMetaData)
                QApplication.processEvents()
                self.writeImage()
                dialog.update_progress_signal.emit(i)
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
