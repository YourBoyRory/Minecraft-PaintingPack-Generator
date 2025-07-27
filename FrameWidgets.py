from PyQt5.QtCore import Qt, QUrl, QSize, QTimer, QStringListModel, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage, QIcon, QColor, QFont, QWheelEvent
from PyQt5.QtWidgets import QScrollArea, QSlider, QMainWindow, QMessageBox, QMenuBar, QDialog, QColorDialog, QFormLayout, QLineEdit, QMenu, QAction, QListWidgetItem, QListWidget, QTabWidget, QApplication, QWidget, QVBoxLayout, QComboBox, QLabel, QFrame, QHBoxLayout, QFileDialog, QSizePolicy, QSpinBox, QPushButton
from PyQt5.QtWidgets import QApplication, QCheckBox, QStyleFactory, QProgressBar, QGraphicsView, QGraphicsScene, QGraphicsTextItem
from FrameDialog import LoadingDialog
from PaintingGenerator import PaintingGenerator
from ResourcePackBuilder import ResourcePackBuilder
from pathlib import Path
from io import BytesIO
from PIL import Image
import hashlib
import traceback
import platform
import requests
import json
import copy
import sys
import os

class ViewPort(QGraphicsView):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.displayingImage = False
        self.current_zoom = 0.4 # start zoom
        self.minZoom = 0.1
        self.maxZoom = 3.0
        self.setAcceptDrops(True)

        # File storages types, because im stupid can cant figure out how to convert between
        self.currentImage = None

    def getCurrentImage(self):
        return self.currentImage

    def setCurrentImage(self, image):
        self.currentImage = image

    def updateViewPort(self):
        pil_image = self.currentImage.convert("RGB")
        data = pil_image.tobytes("raw", "RGB")
        qim = QImage(data, pil_image.width, pil_image.height, QImage.Format_RGB888)
        pixmap = QPixmap(QPixmap.fromImage(qim))
        width = 1024
        height = 1024
        if not self.parent.keepPaintingSize_checkBox.isChecked():
            size_split = size.split('x')
            if len(size_split) < 2:
                size_split = ["2","2"]
            width = 256*int(size_split[0])
            height = 256*int(size_split[1])
        self.loadImage(pixmap.scaled(width, height, Qt.KeepAspectRatio))

    def wheelEvent(self, event: QWheelEvent):
        if not self.parent.view_slider.isEnabled():
            event.ignore()
            return
        # Get the wheel delta (positive for scrolling up, negative for scrolling down)
        angle_delta = event.angleDelta().y()
        factor = 1.2
        # Determine the zoom factor (scale in and scale out)
        if angle_delta > 0:
            # Zoom in
            zoom = min(self.current_zoom * factor, self.maxZoom)
        else:
            # Zoom out
            zoom = max(self.current_zoom / factor, self.minZoom)

        self.parent.view_slider.setValue(int(zoom * 100))
        event.accept()  # Mark the event as handled

    def setZoom(self, zoom):
        if self.displayingImage:
            self.resetTransform()
            self.scale(zoom , zoom)
        #print(zoom)
        self.current_zoom = zoom


    def loadImage(self, pixmap):
        self.displayingImage = True
        self.setZoom(self.current_zoom)
        self.setDragMode(QGraphicsView.ScrollHandDrag)

        scene = QGraphicsScene(self)
        scene.addPixmap(pixmap)
        self.setScene(scene)

        # Optionally, set the scene's background color
        #self.currScene.setBackgroundBrush(Qt.white)

    def displayText(self, text):
        self.displayingImage = False
        self.resetTransform()
        self.setDragMode(QGraphicsView.NoDrag)
        # Create and add text item to the scene
        text_item = QGraphicsTextItem(text)
        font = QFont("Sans", 16)
        text_item.setFont(font)
        text_item.setDefaultTextColor(Qt.white)

        # Center the text in the scene
        text_item.setPos(200, 250)  # Adjust the position to suit your needs

        # Add the text item to the scene
        scene = QGraphicsScene(self)
        scene.setObjectName("IgnoreMin")
        scene.addItem(text_item)
        self.setScene(scene)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        self.parent.dropEvent(event)

class OptionsPanel(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.lock = True

        init_silder_value = 500
        self.view_size = int(100 + (init_silder_value / 500) * 300)

        self.paintings = {}
        self.used_paintings = []
        self.options = {}

        PaintingOptions_layout = QVBoxLayout()

        """ Detail """
        lable_width = 120
        detail_layout = QHBoxLayout()
        self.detail_spin_box = QSpinBox(self)
        self.detail_spin_box.setRange(1, 16)  # Set the valid range (1 to 100)
        self.detail_spin_box.setValue(1)  # Set the initial value
        detail_label = QLabel('Detail: ')
        detail_label.setMaximumWidth(lable_width)
        detail_layout.addWidget(detail_label)
        detail_layout.addWidget(self.detail_spin_box)

        """ Scale Method """
        scale_layout = QHBoxLayout()
        self.scale_combo_box = QComboBox(self)
        scale_label = QLabel('Scale Method: ')
        scale_label.setMaximumWidth(lable_width)
        scale_layout.addWidget(scale_label)
        self.scaleOptions = ["Stretch", "Fit", "Crop"]
        self.scale_combo_box.addItems(self.scaleOptions)
        scale_layout.addWidget(self.scale_combo_box)

        """ Backgroud Color """
        color_button_layout = QHBoxLayout()
        self.color_button = QPushButton('Choose Backgroud Color', self)
        self.color_button.clicked.connect(self.showColorDialog)
        color_button_layout.addWidget(self.color_button)

        """ Painting Size """
        size_layout = QHBoxLayout()
        self.size_combo_box = QComboBox(self)
        size_label = QLabel('Painting Size: ')
        size_label.setMaximumWidth(lable_width)
        size_layout.addWidget(size_label)
        size_layout.addWidget(self.size_combo_box)

        """ Painting """
        painting_layout = QHBoxLayout()
        self.painting_combo_box = QComboBox(self)
        painting_label = QLabel('Painting: ')
        painting_label.setMaximumWidth(lable_width)
        painting_layout.addWidget(painting_label)
        painting_layout.addWidget(self.painting_combo_box)

        """ Frame """
        frame_layout = QHBoxLayout()
        self.frame_combo_box = QComboBox(self)
        frame_label = QLabel('Frame: ')
        frame_label.setMaximumWidth(lable_width//2)
        frame_layout.addWidget(frame_label)
        frame_layout.addWidget(self.frame_combo_box)

        # Populate Data
        self.options['detail'] = self.detail_spin_box.value()
        self.options['background_color'] = "#000000"
        self.options['scale_method'] = self.scale_combo_box.currentText()
        self.options['size'] = self.size_combo_box.currentText()
        self.updateComboBox()
        self.options['frameName'] = self.frame_combo_box.currentText()
        self.options['paintingName'] = self.painting_combo_box.currentText()

        self.detail_spin_box.valueChanged.connect(self.updateDetail)
        self.size_combo_box.currentIndexChanged.connect(self.updateSize)
        self.painting_combo_box.currentIndexChanged.connect(self.updatePainting)
        self.scale_combo_box.currentIndexChanged.connect(self.updateScale)
        self.frame_combo_box.currentIndexChanged.connect(self.updateFrame)

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
        self.setLayout(PaintingOptions_layout)
        self.setMinimumWidth(250)
        self.setMaximumWidth(350)

        self.lock = False

    def reset(self, paintings):
        self.paintings = paintings
        self.size_combo_box.clear()
        for key in self.paintings:
            self.size_combo_box.addItem(key)
        self.updateComboBox()

    def getData(self):
        return self.options

    def setData(self, data=None):
        self.lock = True
        if data != None:
            self.options = data
        self.detail_spin_box.setValue(self.options["detail"])
        self.scale_combo_box.setCurrentText(self.options["scale_method"])
        self.size_combo_box.setCurrentText(self.options["size"])
        self.painting_combo_box.setCurrentText(self.options["paintingName"])
        self.frame_combo_box.setCurrentText(self.options["frameName"])
        self.lock = False
        self.updateComboBox()

    def addPainting(self, data):
        size = data['size']
        name = data['paintingName']
        if name in self.used_paintings:
            self.used_paintings.remove(name)
        self.updateSizeComboBox()
        self.updateComboBox()
        self.updateFrameComboBox()

    def removePainting(self, data):
        size = data['size']
        name = data['paintingName']
        if name not in self.used_paintings:
            self.used_paintings.append(name)
        self.updateSizeComboBox()
        self.updateComboBox()
        self.updateFrameComboBox()

    def updateSizeComboBox(self):
        self.lock = True
        current_selection = self.size_combo_box.currentText()
        self.size_combo_box.clear()
        for size in self.paintings:
            if not all(item in self.used_paintings for item in self.paintings[size]):
                self.size_combo_box.addItem(size)
        self.size_combo_box.setCurrentText(current_selection)
        self.lock = False

    def updateFrameComboBox(self):
        self.lock = True
        if self.frame_combo_box.currentText() != "None":
            self.frame_combo_box.setCurrentText(self.painting_combo_box.currentText())
        self.lock = False

    def updateComboBox(self):
        size = self.options['size']
        self.lock = True
        self.frame_combo_box.clear()
        self.painting_combo_box.clear()
        if size != "":
            # Update frame box
            for types in self.paintings[size]:
                self.frame_combo_box.addItem(types)
                if types not in self.used_paintings:
                    self.painting_combo_box.addItem(types)
            self.frame_combo_box.addItem("None")
        else:
            print("No Paintings left.")
        self.lock = False

    def showColorDialog(self):
        color = QColorDialog.getColor(QColor(self.options['background_color']))
        if color.isValid():
            self.options['background_color'] = color.name()
        self.parent.requestViewPortDraw()

    def updateDetail(self):
        self.options['detail'] = self.detail_spin_box.value()
        if not self.lock:
            self.parent.requestViewPortDraw()

    def updateScale(self):
        self.options['scale_method'] = self.scale_combo_box.currentText()
        if not self.lock:
            self.parent.requestViewPortDraw()

    def updateSize(self):
        self.options['size'] = self.size_combo_box.currentText()
        if not self.lock:
            self.updateComboBox()
            self.parent.requestViewPortDraw()

    def updatePainting(self):
        self.options['paintingName'] = self.painting_combo_box.currentText()
        if not self.lock:
            self.updateFrameComboBox()
            self.parent.requestViewPortDraw()

    def updateFrame(self):
        self.options['frameName'] = self.frame_combo_box.currentText()
        if not self.lock:
            self.parent.requestViewPortDraw()

class PaintingEditor(QWidget):

    def __init__(self, parent):
        super().__init__(parent)

        # This is very OOP thus its ok and cool
        self.parent = parent
        self.packConrols = self.parent.packConrols

        self.META_NAME = ""
        self.META_DATA = {}

        self.generationThread = QTimer(self)
        self.generationThread.timeout.connect(self.generateImage)
        self.generationThread.setSingleShot(True)

        self.notifyTimer = QTimer()
        self.notifyTimer.setSingleShot(True)

        self.currentBigImage = None

        init_silder_value = 500
        self.view_size = int(100 + (init_silder_value / 500) * 300)

        self.file_path_stack = []
        self.lock = True
        self.updating = False
        self.backgroundColor = "#000000"

        PaintingEditor_Layout = QVBoxLayout()
        combine_OptionsViewport = QHBoxLayout()
        """Options Panel"""
        self.optionsPanel = OptionsPanel(self)
        combine_OptionsViewport.addWidget(self.optionsPanel)

        """View Port"""
        self.viewPort = ViewPort(self)
        self.viewPort.displayText("Drop image here to customize your painting")
        combine_OptionsViewport.addWidget(self.viewPort)
        PaintingEditor_Layout.addLayout(combine_OptionsViewport)
        self.viewPort.setMinimumWidth(600)

        """Tool Bar"""
        ToolBar = QWidget()
        ToolBar.setObjectName("Frame")
        ToolBar_layout = QVBoxLayout()
        # View Port Tools
        tools_layout = QHBoxLayout()
        self.toolbarText = " "
        self.path_label = QLabel(self.toolbarText, self)
        self.path_label.setMinimumWidth(1)
        #self.path_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
        self.keepPaintingSize_checkBox = QCheckBox('Auto Scale', self)
        self.keepPaintingSize_checkBox.setChecked(True)
        self.keepPaintingSize_checkBox.stateChanged.connect(self.requestViewPortDraw)
        self.view_slider = QSlider(Qt.Horizontal)
        minS = int(self.viewPort.minZoom * 100)
        maxS = int(self.viewPort.maxZoom * 100)
        self.view_slider.setRange(minS, maxS)  # Set minimum value
        self.view_slider.setValue(int(self.viewPort.current_zoom * 100))  # Set initial value
        self.view_slider.setTickPosition(QSlider.TicksBelow)
        self.view_slider.setTickInterval((maxS-minS)//6)
        self.view_slider.setFixedWidth(100)
        self.view_slider.setMaximumWidth(150)
        self.view_slider.valueChanged.connect(self.view_slider_changed)
        tools_layout.addWidget(self.path_label)
        tools_layout.addStretch()
        tools_layout.addWidget(self.keepPaintingSize_checkBox)
        tools_layout.addWidget(self.view_slider)
        #Add Layouts
        ToolBar_layout.addLayout(tools_layout)
        ToolBar.setLayout(ToolBar_layout)
        PaintingEditor_Layout.addWidget(ToolBar)
        self.setLayout(PaintingEditor_Layout)

    def loadPaintings(self):
        try:
            pack_format = self.packConrols.packData['meta']['pack']['pack_format']
        except:
            print("format unset defaulting to demo mode")
            pack_format = 65535 # idk man
        with open(self.resource_path('paintings.json'), 'r') as file:
            json_in = json.load(file)
            master_list = {}
            for format_num, data in json_in.items():
                if int(format_num) <= int(pack_format):
                    #REMOVE_print(format_num, pack_format)
                    for size, paint_list in data.items():
                        if size in master_list:
                            master_list[size] += paint_list
                        else:
                            master_list[size] = paint_list
            paintings = dict(sorted(master_list.items()))
        return paintings

    def newPack(self):
        self.painting_maker = PaintingGenerator()
        self.reset()

    def dropEvent(self, event):
        # Get the dropped file path
        for file in event.mimeData().urls():
            ext = Path(file.toLocalFile()).name.split(".")[1].lower()
            if ext == "pson" or ext == "json":
                self.parent.loadFromFile(file.toLocalFile())
                return
            if self.packConrols.packCreated == True:
                self.file_path_stack.append(file)
                self.init_stack_count = len(self.file_path_stack)
            else:
                QMessageBox.information(self, "Pack not Created", f"Please create a pack before importing images.")
                return
        self.lock = False
        self.getNextImage()

    def reset(self):
        self.parent.setButtonEnabled(False)
        self.optionsPanel.reset(self.loadPaintings())
        self.viewPort.displayText("Drop image here to customize your painting")
        self.setToolbarText("")
        self.view_size = 400

    def notify(self, msg, interval=2000):
        if self.notifyTimer.isActive():
            self.notifyTimer.stop()
        self.notifyTimer = QTimer()
        self.notifyTimer.setSingleShot(True)
        self.path_label.setText(msg)
        self.notifyTimer.setInterval(interval)
        self.notifyTimer.timeout.connect(lambda: self.setToolbarText())
        self.notifyTimer.start()

    def setToolbarText(self, msg=None):
        if msg != None:
            self.toolbarText = msg
        if not self.notifyTimer.isActive():
            self.path_label.setText(self.toolbarText)

    def view_slider_changed(self):
        zoom = self.view_slider.value() / 100
        self.viewPort.setZoom(zoom)

    def setButtonEnabled(self, value):
        self.view_slider.setEnabled(value)
        return

    def setCurrentImage(self, file_path):
        # Put loaded image on the file stack
        self.file_path_stack.append(QUrl(file_path))
        self.init_stack_count = len(self.file_path_stack)
        # Process image
        self.lock = False
        self.getNextImage()

    def getCurrentImageData(self):
        options_data = self.optionsPanel.getData()
        imageData = options_data
        imageData['file_path'] = self.art_url
        return imageData, self.getCurrentImage()

    def getCurrentImage(self):
        return self.viewPort.getCurrentImage()

    def getNextImage(self):
        #REMOVE_print(self.file_path_stack)
        if len(self.file_path_stack) > 0:
            try:
                url = self.file_path_stack.pop()
                if url.toLocalFile() == "":
                    self.art_path = url.toString()
                    self.art_url = url.toString()
                    response = requests.get(self.art_path)
                    img_data = BytesIO(response.content)
                    imageLoad = img_data
                    #REMOVE_print(response.status_code)
                else:
                    self.art_path = url.toLocalFile()
                    imageLoad = self.art_path
                    self.art_url = url.toString()

                file_name = Path(self.art_path).name.split(".")[0].lower()
                self.generateImage(imageLoad)
                self.viewPort.updateViewPort()
                self.autoSetComboBoxes(file_name)
                curr = self.init_stack_count-len(self.file_path_stack)
                self.setToolbarText(f"File: [{curr}/{self.init_stack_count}] - {self.art_path}")
                self.parent.setButtonEnabled(True)
            except Exception as e:
                self.getNextImage()
                self.viewPort.displayText(f"Failed to open image: {str(e)}")
                traceback.print_exc()
                self.setToolbarText(" ")
        else:
            self.init_stack_count = 0
            print("Stack is empty.")
            self.lock = True
            #self.updateComboBox()
            self.parent.setButtonEnabled(False)
            self.viewPort.displayText("Drop Next image here")
            self.setToolbarText(" ")

    def generateImage(self, image=None, options=None):
        # Load image
        if image != None:
            self.currentBigImage = Image.open(image)
        # Getting Options
        if options == None:
            options = self.optionsPanel.options
        detail = options['detail']
        scale_method = options['scale_method']
        size = options['size']
        painting = options['paintingName']
        frame = options['frameName']
        background_color = options['background_color']

        if frame == "None":
            showFrame = False
            frameName = painting
        else:
            showFrame = True
            frameName = frame

        currentImage = self.painting_maker.makePaiting(detail, scale_method, background_color, frameName, showFrame, self.currentBigImage)
        self.viewPort.setCurrentImage(currentImage)
        self.viewPort.updateViewPort()

    def requestViewPortDraw(self):
        if self.generationThread.isActive():
            return
        if self.lock == True:
            return
        try:
            self.generateImage()
            #self.generationThread.start(16) # 16ms frame delta, limit to 60fps
        except Exception as e:
            self.viewPort.displayText(f"Failed to open image: {str(e)}")
            traceback.print_exc()

    def autoSetComboBoxes(self, filename):
        return
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
            self.setMetaData()
        except:
            #REMOVE_print("WARN: Failed to parse auto values")
            pass

    def resource_path(self, file):
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(__file__)
        return os.path.join(base_path, 'assets', file)

class packAssetList(QListWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

        self.setSelectionMode(3)
        self.setContextMenuPolicy(3)
        font = QFont()
        font.setPointSize(9)
        self.setFont(font)

        self.assets = {}

    def getAsset(self, asset):
        asset_id = self.listwidget.row(asset)
        return self.assets[asset_id], asset_id

    def addAsset(self, asset_title, asset_body, assetData, assetPixmap):

        asset_text = f"{asset_title}\n{asset_body}"
        asset_id = asset_text

        asset = QListWidgetItem(asset_text)
        asset.setIcon(QIcon(assetPixmap))  # Set QPixmap as an icon
        self.addItem(asset)
        self.setIconSize(QSize(100, 100))

        self.assets[asset_id] = copy.deepcopy(assetData)

        #print(json.dumps(self.assets, indent=2))

    def removeAsset(self, asset):
        self.changesSaved = False
        asset_id = asset.text()
        filename = self.assets[asset_id]['paintingName']
        print(json.dumps(self.assets, indent=2))

        # Remove Entries
        self.parent.pack_builder.delFile(f"assets/minecraft/textures/painting/{filename}.png")
        self.takeItem(self.row(asset))
        deleted_asset_data = self.assets.pop(asset_id, None)
        return deleted_asset_data


class PackControls(QWidget):

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

        self.packCreated = False
        self.saveFile = None
        self.changesSaved = True
        self.used_paintings = {}
        self.packData = {}
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
        self.listwidget = packAssetList(self)
        self.listwidget.customContextMenuRequested.connect(self.showContextMenu)
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

    def reset(self, packData=False):
        self.used_paintings = {}
        if packData:
            self.setPackInfo(packData)
        self.changesSaved = True
        self.saveFile = None
        self.listwidget.clear()

    def setPackInfo(self, packData):
        self.packCreated = True
        self.packData = packData
        self.packName = self.packData['title']
        packMeta = self.packData['meta']
        packIcon = self.packData['icon']
        formatNumber = packMeta['pack']['pack_format']
        packDescription = packMeta['pack']['description']
        self.pack_builder = ResourcePackBuilder(packMeta)
        try:
            pil_image = Image.open(packIcon).convert('RGB')
            pil_image_resized = pil_image.resize((64,64))
            image_bytes = BytesIO()
            pil_image_resized.save(image_bytes, format='PNG')
            image_bytes.seek(0)
            self.pack_builder.addFile("pack.png", image_bytes.read())
            data = pil_image_resized.tobytes("raw", "RGB")
            qim = QImage(data, pil_image_resized.width, pil_image_resized.height, QImage.Format_RGB888)
            pixmap = QPixmap(QPixmap.fromImage(qim))
        except:
            #REMOVE_print("No Image Provided or failed to load")
            pixmap = QPixmap(self.resource_path("pack.png"))
        self.packIcon_label.setPixmap(pixmap.scaled(QSize(100, 100), aspectRatioMode=1))
        self.packTitle_label.setText(f"{self.packName}\nFormat: {formatNumber}\n\n{packDescription}")

    def showContextMenu(self, pos):
        global_pos = self.listwidget.mapToGlobal(pos)
        item = self.listwidget.itemAt(pos)
        context_menu = QMenu(self)
        delete_action = QAction("Delete Painting",  self.listwidget)
        delete_action.triggered.connect(lambda: self.removeImage(item))
        edit_action = QAction("Edit Painting",  self.listwidget)
        edit_action.triggered.connect(lambda: self.editImage(item))
        context_menu.addAction(delete_action)
        context_menu.addAction(edit_action)
        if item == None:
            delete_action.setEnabled(False)
            edit_action.setEnabled(False)
        context_menu.exec_(global_pos)

    def removeImage(self, asset):
        try:
            self.changesSaved = False

            deleted_asset_data = self.listwidget.removeAsset(asset)
            self.parent.addPainting(deleted_asset_data)

            if self.listwidget.count() == 0:
                self.export_button.setEnabled(False)
                self.parent.save_draft_action.setEnabled(False)
            else:
                self.export_button.setEnabled(True)
                self.parent.save_draft_action.setEnabled(True)
        except:
            traceback.print_exc()
            self.notify(f"Error removing entry.")

    def editImage(self, asset):
        try:
            self.changesSaved = False
            deleted_asset_data = self.listwidget.removeAsset(asset)
            self.parent.addPainting(deleted_asset_data)
            self.parent.setData(deleted_asset_data)
            self.parent.setCurrentImage(deleted_asset_data['file_path'])
        except:
            traceback.print_exc()
            self.notify(f"File no longer readable. It may be missing or lack read permissisons.")
            #QMessageBox.information(self, "File Read Error", "File no longer readable. It may be missing or lack read permissisons.")


    def writeImage(self):
        self.changesSaved = False
        #self.parent.lock = True # Lock UI

        # Get the image data
        imageData, paintingPIL = self.parent.getCurrentImageData()
        pil_image = paintingPIL.convert("RGB")
        data = pil_image.tobytes("raw", "RGB")
        qim = QImage(data, pil_image.width, pil_image.height, QImage.Format_RGB888)
        pixmap = QPixmap(QPixmap.fromImage(qim)).scaled(100, 100, Qt.KeepAspectRatio)

        detail = imageData['detail']
        paintingName = imageData['paintingName']
        frameName = imageData['frameName']
        size = imageData['size']
        scale_method = imageData['scale_method']
        backgroundColor = imageData['background_color']

        asset_title = f'{paintingName.title()} ({size})'
        asset_body = f'Frame: {frameName.title()}\n\nDetail: {detail}x\nScale Method: {scale_method}\nBackground Color: {backgroundColor}'

        # Push image to pack
        image_bytes = BytesIO()
        paintingPIL.save(image_bytes, format='PNG')
        image_bytes.seek(0)
        self.pack_builder.addFile(f'assets/minecraft/textures/painting/{paintingName}.png', image_bytes.read())

        # Add to Lists
        self.listwidget.addAsset(asset_title, asset_body, imageData, pixmap)
        self.parent.removePainting(imageData)

        # Reset UI
        self.parent.getNextImage()

    def exportPack(self):
        try:
            if platform.system() == 'Windows':
                base = os.getenv('APPDATA')
            elif platform.system() == 'Linux':
                base = os.getenv('HOME')
            initial_directory = os.path.join(base, '.minecraft', 'resourcepacks')
            if not Path(initial_directory).exists():
                initial_directory = os.path.join(os.path.expanduser("~"), "Documents")
        except:
            initial_directory = os.path.join(os.path.expanduser("~"), "Documents")
        directory = os.path.join(initial_directory, f"{self.packName}.zip")
        file, _ = QFileDialog.getSaveFileName(self.parent, "Save Resource Pack", directory, "MC Resource Pack (*.zip);;All Files (*)")
        if file:
            self.pack_builder.writePack(file)
            self.notify(f"Resource Pack saved to {file}")
            #QMessageBox.information(self, "Pack Saved", f"Resource Pack saved to\n{file}")

    def openDraft(self, file_name):
        with open(file_name) as f:
            loaded_paintings = json.load(f)
        if 'paintings' not in loaded_paintings:
            self.loadDraft(loaded_paintings)
        else:
            self.loadDraft(loaded_paintings['paintings'])
        self.saveFile = file_name
        self.changesSaved = True


    def loadDraft(self, loaded_paintings):
        self.changesSaved = False
        dialog = LoadingDialog(self)
        i=1
        self.reset()
        self.parent.reset()
        dialog.show_loading(len(loaded_paintings))
        self.lock = False
        failedPaintings = ""
        failedCount = 0
        self.used_paintings = {}
        for paintingName in loaded_paintings:
            paintingMetaData = loaded_paintings[paintingName]
            #print(paintingName, paintingMetaData)
            #try:
            self.used_paintings[paintingName] = loaded_paintings[paintingName]
            #self.used_paintings.pop(paintingName, None) # why do i do this?
            self.parent.setCurrentData(paintingName, paintingMetaData)
            self.parent.setCurrentImage(paintingMetaData['file_path'])
            self.parent.setCurrentData(paintingName, paintingMetaData)
            QApplication.processEvents()
            self.writeImage()
            dialog.update_progress_signal.emit(i)
            i+=1
            #except:
            #    if failedCount < 4:
            #        path = paintingMetaData['file_path']
            #        failedPaintings += f"    {path}\n"
            #    failedCount += 1
        if failedPaintings != "":
            if failedCount > 4:
                failedPaintings += f"    And {failedCount-4} more...\n"
            QMessageBox.warning(self, "File Read Error", f"The following files are no longer readable:\n{failedPaintings}\nThey may be missing or lack read permissisons.")
        with open("loaded_paintings.json", "w") as fp:
                json.dump(loaded_paintings, fp, indent=4)
        with open("Mem_dump.json", "w") as fp:
                json.dump(self.used_paintings, fp, indent=4)
        dialog.close_dialog()

    def saveDraft(self, file=False):
        directory = os.path.join(os.path.expanduser("~"), "Documents", f"{self.packName}.pson")
        if not file:
            file, _ = QFileDialog.getSaveFileName(self.parent, "Save Draft", directory, "PaintingStudio Draft (*.pson)")
        if file:
            self.saveFile = file
            self.changesSaved = True
            dump = {
                'pson': self.packData,
                'paintings': self.used_paintings
            }
            with open(file, "w") as fp:
                json.dump(dump, fp, indent=4)
            self.notify(f"Draft saved to {file}")
            traceback.print_exc()
            #QMessageBox.information(self, "Draft Saved", f"Draft saved to\n{file}")

    def notify(self, msg, interval=2000):
        self.parent.notify(msg, interval)

    def resource_path(self, file):
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(__file__)
        return os.path.join(base_path, 'assets', file)
