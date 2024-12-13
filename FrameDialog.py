from PyQt5.QtCore import Qt, QUrl, QSize, QTimer, QStringListModel, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage, QIcon, QColor, QFont
from PyQt5.QtWidgets import QScrollArea, QSlider, QMainWindow, QMessageBox, QMenuBar, QDialog, QColorDialog, QFormLayout, QLineEdit, QMenu, QAction, QListWidgetItem, QListWidget, QTabWidget, QApplication, QWidget, QVBoxLayout, QComboBox, QLabel, QFrame, QHBoxLayout, QFileDialog, QSizePolicy, QSpinBox, QPushButton
from PyQt5.QtWidgets import QApplication, QStyleFactory, QProgressBar

class LoadingDialog(QDialog):
    # Define a signal to update progress
    update_progress_signal = pyqtSignal(int)

    def __init__(self, parent):
        super().__init__(parent)

        # Initialize the dialog window
        self.setWindowTitle("Opening Draft")
        self.setModal(True)
        self.setFixedSize(300, 100)

        self.setWindowFlags(Qt.Dialog)

        # Create the progress bar
        self.progressBar = QProgressBar(self)

        # Set layout for the dialog
        layout = QVBoxLayout(self)
        layout.addWidget(self.progressBar)

        # Connect the signal to the slot method
        self.update_progress_signal.connect(self.update_progress)

    def update_progress(self, value):
        """Slot to update the progress bar"""
        self.progressBar.setValue(value)

    def show_loading(self, value):
        """Show the dialog (non-modal)"""
        self.progressBar.setRange(0, value)
        self.progressBar.setValue(0)
        self.show()  # This will show the dialog non-modally

    def close_dialog(self):
        """Method to close the dialog"""
        self.close()  # Close the dialog

class InputDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.icon = None
        self.setWindowTitle("Create New Pack")
        self.setModal(True)
        self.setObjectName("Frame")
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
