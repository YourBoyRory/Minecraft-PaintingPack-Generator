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
from FrameDialog import LoadingDialog, InputDialog
from FrameWidgets import PackControls

class PaintingStudio(QMainWindow):

    def __init__(self):
        super().__init__()
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        layout = QHBoxLayout(self)
        self.central_widget.setLayout(layout)
        init_silder_value = 500
        self.view_size = int(100 + (init_silder_value / 500) * 300)

        with open(self.resource_path('paintings.json'), 'r') as file:
            self.paintings = json.load(file)
        self.used_paintings = {}
        self.file_path_stack = []
        self.lock = True
        self.updating = False
        self.packCreated = False
        self.backgroundColor = "#000000"

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


        """Options Pane"""
        PaintingOptions = QWidget()
        PaintingOptions_layout = QVBoxLayout()

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
        self.scale_combo_box.currentIndexChanged.connect(self.updateImage)
        self.frame_combo_box.currentIndexChanged.connect(self.updateImage)

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


        """Main Window"""

        ViewPort.setMinimumWidth(600)
        PaintingOptions.setMinimumWidth(250)
        PaintingOptions.setMaximumWidth(350)
        self.packConrols.setMinimumWidth(250)
        self.packConrols.setMaximumWidth(350)

        combine_OptionsViewport = QHBoxLayout()
        combine_ViewportToolbar = QVBoxLayout()

        combine_OptionsViewport.addWidget(PaintingOptions)
        combine_OptionsViewport.addWidget(ViewPort)
        combine_ViewportToolbar.addLayout(combine_OptionsViewport)
        combine_ViewportToolbar.addWidget(ToolBar)
        layout.addLayout(combine_ViewportToolbar)
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
            self.packCreated = True
            self.painting_maker = PaintingGenerator()

            #remove self. later
            self.packName = title
            packMeta = {
                "pack": {
                    "description": f"{description}",
                    "pack_format": number
                }
            }
            self.packConrols.setPackInfo(title, packMeta, icon)

            self.used_paintings = {}
            self.size_combo_box.clear()
            for key in self.paintings:
                self.size_combo_box.addItem(key)
            self.updateComboBox()


    def view_slider_changed(self):
        self.update_view_size()
        self.updateImage()

    def update_view_size(self, autoScale = False):
        value = self.view_slider.value()
        if value <= 500:
            # Bottom half (100 to 400)
            self.view_size = int(100 + (value / 500) * 300)
        else:
            # Top half (400 to 1600)
            self.view_size = int(400 + ((value - 500) / 500) * 1200)
        self.image_label.setFixedSize(self.view_size, self.view_size)

    def resource_path(self, relative_path):
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

    def setButtonEnabled(self, value):
        if self.packConrols.listwidget.count() == 0:
            self.packConrols.export_button.setEnabled(False)
            self.save_draft_action.setEnabled(False)
        else:
            self.packConrols.export_button.setEnabled(True)
            self.save_draft_action.setEnabled(True)
        self.packConrols.add_button.setEnabled(value)
        self.view_slider.setEnabled(value)
        return
        self.detail_spin_box.setEnabled(value)
        self.size_combo_box.setEnabled(value)
        self.painting_combo_box.setEnabled(value)
        self.frame_combo_box.setEnabled(value)
        self.scale_combo_box.setEnabled(value)

        self.color_button.setEnabled(value)

    def editImage(self, item):
        try:
            name = item.text().split()[0].lower()
            size = item.text().split()[1].replace("(", "").replace(")", "")
            self.pack_builder.delFile(f"assets/minecraft/textures/painting/{name}.png")
            self.packConrols.listwidget.takeItem(self.packConrols.listwidget.row(item))
            if self.size_combo_box.findText(size) == -1:
                self.size_combo_box.addItem(size)
            if self.packConrols.listwidget.count() == 0:
                self.packConrols.export_button.setEnabled(False)
                self.save_draft_action.setEnabled(False)
            else:
                self.packConrols.export_button.setEnabled(True)
            self.loadImageFromSaved(name)
        except Exception as e:
            print(f"Failed to edit image: {str(e)}")

    def loadFromFile(self):
        dialog = LoadingDialog(self)
        file_name, _ = QFileDialog.getOpenFileName(self, 'Load Draft', '', 'PaintingStudio Draft (*.json)')
        if file_name:
            self.packConrols.listwidget.clear()
            self.used_paintings = {}
            self.updateComboBox()
            with open(file_name) as f:
                loaded_paintings = json.load(f)
            i=1
            dialog.show_loading(len(loaded_paintings))
            for paintingName in loaded_paintings:
                self.used_paintings[paintingName] = loaded_paintings[paintingName]
                self.loadImageFromSaved(paintingName)
                self.writeImage()
                dialog.update_progress_signal.emit(i)
                QApplication.processEvents()
                i+=1
            dialog.close_dialog()

    def saveToFile(self):
        options = QFileDialog.Options()
        file, _ = QFileDialog.getSaveFileName(self, "Save Draft", f"{self.packName}.json", "PaintingStudio Draft (*.json)", options=options)
        if file:
            with open(file, "w") as fp:
                json.dump(self.used_paintings, fp)
            QMessageBox.information(self, "Draft Saved", f"Draft saved to\n{file}")

    def loadImageFromSaved(self, paintingName):
        detail = self.used_paintings[paintingName]["detail"]
        frameName = self.used_paintings[paintingName]["frame"]
        size = self.used_paintings[paintingName]["size"]
        scale_method = self.used_paintings[paintingName]["scale_method"]
        background_color = self.used_paintings[paintingName]["background_color"]
        file_path = self.used_paintings[paintingName]["file_path"]

        if paintingName in self.used_paintings:
            self.used_paintings.pop(paintingName, None)
            self.updateComboBox()

        self.file_path_stack.append(QUrl(f'file://{file_path}'))
        self.init_stack_count = len(self.file_path_stack)
        self.handle_dropped_image()

        self.backgroundColor = background_color
        self.scale_combo_box.setCurrentText(scale_method)

        self.size_combo_box.setCurrentText(size)
        self.painting_combo_box.setCurrentText(paintingName)
        self.frame_combo_box.setCurrentText(frameName)
        self.detail_spin_box.setValue(detail)

    def getCurrentImageData(self):
        paintingName = self.painting_combo_box.currentText()
        imageData = {}
        imageData[paintingName] = {}
        imageData[paintingName]['detail']  = self.detail_spin_box.value()
        imageData[paintingName]['frameName'] = self.frame_combo_box.currentText()
        imageData[paintingName]['size'] = self.size_combo_box.currentText()
        imageData[paintingName]['scale_method'] = self.scale_combo_box.currentText()
        imageData[paintingName]['backgroun_color'] = self.backgroundColor
        imageData[paintingName]['frame_index'] = self.frame_combo_box.currentIndex()
        return imageData, paintingName, self.art

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
                print(file)
            self.init_stack_count = len(self.file_path_stack)
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

    def prog_help(self):
        pass

    def handle_dropped_image(self):
        if len(self.file_path_stack) > 0:
            try:
                url = self.file_path_stack.pop()
                self.lock = False
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
                self.autoSetComboBoxes(file_name)
                curr = self.init_stack_count-len(self.file_path_stack)
                self.path_label.setText(f"File: [{curr}/{self.init_stack_count}] - {self.art_path}")
                self.updateImage()
                self.setButtonEnabled(True)
            except Exception as e:
                self.lock = True
                self.handle_dropped_image()
                self.image_label.setText(f"Failed to open image: {str(e)}")
        else:
            self.init_stack_count = 0
            print("Stack is empty.")

    def autoSetComboBoxes(self, filename):
        try:
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

    def pushImageUpdate(self):
        if self.lock == False:
            # Open the image using Pillow
            self.update_view_size()
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

            # Convert the image to QPixmap for display
            pil_image = self.painting.convert("RGB")
            data = pil_image.tobytes("raw", "RGB")
            qim = QImage(data, pil_image.width, pil_image.height, QImage.Format_RGB888)
            pixmap = QPixmap(QPixmap.fromImage(qim))
            # Display the image at full size in the label
            self.image_label.setPixmap(pixmap.scaled(QSize(self.view_size, self.view_size), aspectRatioMode=1))
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
        if self.frame_combo_box.currentText() != "None":
            self.frame_combo_box.setCurrentText(self.painting_combo_box.currentText())

    def resource_path(self, file):
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(__file__)
        return os.path.join(base_path, 'assets', file)

    def updateComboBox(self):
        self.updating = True
        size = self.size_combo_box.currentText()
        self.frame_combo_box.clear()
        self.painting_combo_box.clear()
        if size == "":
            print("No Paintings.")
            return
        for types in self.paintings[size]:
            self.frame_combo_box.addItem(types)
            if types not in self.used_paintings:
                self.painting_combo_box.addItem(types)
        self.frame_combo_box.addItem("None")
        if self.painting_combo_box.currentText() == "":
            self.size_combo_box.removeItem(self.size_combo_box.currentIndex())
        try:
            self.pushImageUpdate()
        except Exception as e:
            print(f"Failed to open image: {str(e)}")
        self.updating = False

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
