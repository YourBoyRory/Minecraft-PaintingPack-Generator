from PyQt5.QtWidgets import QApplication, QMainWindow, QDoubleSpinBox, QVBoxLayout, QWidget
import math

class PackSpinBox(QDoubleSpinBox):
    def __init__(self, format_limit, current_value):
        super().__init__()
        self.stepping=False
        self.release_formats = [4, 5, 6, 7, 8, 9, 12, 13, 15, 18, 22, 32, 34, 42, 46, 55, 63, 64, 65.2]
        self.setRange(format_limit, 65535)
        self.setValue(current_value)  # Set initial value from list
        self.textChanged.connect(self.setStep)
        self.setStep()

    def setStep(self):
        if not self.stepping:
            current_value = self.value()
            if current_value > 64.9:
                self.setDecimals(1)
            else:
                self.setValue(math.floor(current_value))
                self.setDecimals(0)

    def stepBy(self, steps):
        self.stepping=True
        current_value = self.value()

        if current_value > self.release_formats[-1] or (current_value == self.release_formats[-1] and steps == 1):
            self.setValue(current_value + 0.1 * steps)
        else:
            if steps > 0:
                new_value = self.findUpStep(current_value)
            else:
                new_value = self.findDownStep(current_value)
            if new_value  > 64.9:
                self.setDecimals(1)
            else:
                self.setDecimals(0)
            self.setValue(new_value)
        self.stepping=False

    def findUpStep(self, target):
        for num in self.release_formats:
            if num > target:
                return num
        return target

    def findDownStep(self, target):
        for num in reversed(self.release_formats):
            if num < target:
                return num
        return target

