from asyncio import sleep
import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
                             QPushButton, QListWidget, QListWidgetItem, QTextEdit,
                             QLineEdit, QFormLayout, QScrollArea, QGroupBox, QComboBox, QMainWindow)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, pyqtSignal
from datetime import datetime
from PyQt5.QtCore import QTimer


class Item:
    def __init__(self, name, value, unit, is_choice=False, choices=None):
        self.name = name
        self.value = value
        self.unit = unit
        self.is_choice = is_choice
        self.choices = choices if choices else []


class FullScreenImageWindow(QMainWindow):
    def __init__(self, pixmap, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Imagen en Pantalla Completa")
        self.label = QLabel()
        self.label.setPixmap(pixmap)
        self.setCentralWidget(self.label)
        self.showMaximized()

    def mousePressEvent(self, event):
        self.close()


class ChemicalProcessInterface(QWidget):
    # Definir señales personalizadas
    parameter_modified = pyqtSignal(Item, str)
    button_clicked = pyqtSignal(str)

    # Buffer de atributos modificados por el usuario
    changes = []

    def __init__(self, modifiable_items, non_modifiable_items):
        super().__init__()
        self.modifiable_items = modifiable_items
        self.non_modifiable_items = non_modifiable_items
        self.initUI()

    def initUI(self):
        # Layouts
        self.main_layout = QVBoxLayout()  # Cambiado de QHBoxLayout a QVBoxLayout para alinear verticalmente
        self.top_layout = QHBoxLayout()
        self.bottom_layout = QVBoxLayout()

        self.left_layout = QVBoxLayout()
        self.right_layout = QVBoxLayout()

        # Top Left - Parameters List with Scroll Area
        self.param_form_layout = QFormLayout()
        self.param_inputs = {}

        self.update_parameter_form(self.modifiable_items, self.non_modifiable_items)

        self.parameters_group = QGroupBox("Parámetros")
        self.parameters_group.setLayout(self.param_form_layout)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.parameters_group)

        self.left_layout.addWidget(self.scroll_area)

        # Bottom Left - Buttons
        button_layout = QHBoxLayout()
        self.prev_button = QPushButton("Anterior")
        self.next_button = QPushButton("Siguiente")
        self.apply_button = QPushButton("Aplicar")
        button_layout.addWidget(self.prev_button)
        button_layout.addWidget(self.next_button)
        button_layout.addWidget(self.apply_button)
        self.left_layout.addLayout(button_layout)

        # Connect buttons to signal emitters
        self.prev_button.clicked.connect(lambda: self.emit_button_signal("Anterior"))
        self.next_button.clicked.connect(lambda: self.emit_button_signal("Siguiente"))
        self.apply_button.clicked.connect(lambda: self.emit_button_signal("Aplicar"))

        # Top Right - Graphics Display
        self.graphics_display = QLabel()
        self.graphics_display.setFixedSize(520, 380)
        self.graphics_display.setStyleSheet("background-color: white; border: 1px solid black;")
        self.graphics_display.setAlignment(Qt.AlignCenter)
        self.graphics_display.mousePressEvent = self.open_fullscreen_image  # Conectar el evento de clic
        self.right_layout.addWidget(self.graphics_display)

        # Combine top left and right
        self.top_layout.addLayout(self.left_layout, 1)  # Añadido parámetro de estiramiento
        self.top_layout.addLayout(self.right_layout, 1)  # Añadido parámetro de estiramiento

        # Bottom Right - Console Output (ocupa el ancho total ahora)
        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)
        self.console_output.setFixedHeight(300)
        self.bottom_layout.addWidget(self.console_output)

        # Combine layouts
        self.main_layout.addLayout(self.top_layout)
        self.main_layout.addLayout(self.bottom_layout)

        self.setLayout(self.main_layout)
        self.setWindowTitle("Proceso Químico")
        self.resize(1080, 720)

        self.show()

    def emit_button_signal(self, button_name):
        # Emitir señal personalizada cuando se pulsa un botón
        self.button_clicked.emit(button_name)

    def emit_modified_parameter_signal(self, item, newValue):
        # Emitir señal personalizada cuando se modifica un parámetro
        try:
            self.parameter_modified.emit(item, newValue)
        except ValueError:
            # Manejar el error si el valor no es válido
            pass

    def update_graphics(self, image_path):
        pixmap = QPixmap(image_path)
        self.graphics_display.setPixmap(pixmap.scaled(self.graphics_display.size(), Qt.KeepAspectRatio))
        self.current_pixmap = pixmap  # Guardar pixmap actual para usarlo al hacer clic

    def open_fullscreen_image(self, event):
        if hasattr(self, 'current_pixmap'):
            self.fullscreen_window = FullScreenImageWindow(self.current_pixmap)
            self.fullscreen_window.show()

    def append_console_output(self, text, delay=0):
        if delay > 0:
            QTimer.singleShot(delay * 1000, lambda: self._append_text(text))
        else:
            self._append_text(text)

    def _append_text(self, text):
        symbol = "•"
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_text = f"{symbol} [{timestamp}] {text}"
        self.console_output.append(formatted_text)

    def override_console_output(self, text, delay=0):
        if delay > 0:
            QTimer.singleShot(delay * 1000, lambda: self._override_text(text))
        else:
            self.override_text(text)

    def _override_text(self, text):
        symbol = "•"
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_text = f"{symbol} [{timestamp}] {text}"
        self.console_output.setText(formatted_text)

    def delete_console_contents(self):
        self.console_output.clear()

    def apply_modifications(self):
        for item in self.modifiable_items:
            if item.is_choice:
                new_value = self.param_inputs[item.name].currentText()
            else:
                new_value = self.param_inputs[item.name].text()
            try:
                item.value = float(new_value)
                self.append_console_output(f"{item.name} modificado a {item.value} {item.unit}")
            except ValueError:
                self.append_console_output(f"Error al modificar {item.name}: valor no válido")

    def replace_parameter_list(self, new_modifiable_items, new_non_modifiable_items):
        # Reemplazar las listas de parámetros y actualizar la interfaz
        self.modifiable_items = new_modifiable_items
        self.non_modifiable_items = new_non_modifiable_items
        self.update_parameter_form(new_modifiable_items, new_non_modifiable_items)

    def update_parameter_form(self, modifiable_items, non_modifiable_items):
        # Limpiar el layout existente
        for i in reversed(range(self.param_form_layout.count())):
            widget = self.param_form_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()

        # Actualizar el formulario de parámetros con nuevas listas
        self.param_inputs = {}

        for item in modifiable_items:
            if item.is_choice:
                input_field = QComboBox()
                input_field.addItems([str(choice) for choice in item.choices])
                input_field.setCurrentText(str(item.value))
            else:
                input_field = QLineEdit(str(item.value))
            self.param_form_layout.addRow(f"{item.name} ({item.unit}):", input_field)
            self.param_inputs[item.name] = input_field
            if item.is_choice:
                input_field.currentTextChanged.connect(
                    lambda text: self.emit_modified_parameter_signal(item, text))
            else:
                input_field.textChanged.connect(
                    lambda text: self.emit_modified_parameter_signal(item, text))

        for item in non_modifiable_items:
            input_field = QLabel(str(item.value))
            self.param_form_layout.addRow(f"{item.name} ({item.unit}):", input_field)
