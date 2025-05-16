import sys
import math
from PyQt6.QtWidgets import QComboBox
from PyQt6 import QtWidgets, QtCore
from PyQt6.QtCore import QSize, Qt, QRect, QPoint
from PyQt6.QtGui import QIcon, QAction, QColor, QPixmap, QPainter, QImage, QPen, QShortcut, QKeySequence, QFontDatabase
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, \
   QGraphicsColorizeEffect, QToolBar, QSlider, QWidget, QVBoxLayout, QHBoxLayout, QFileDialog, QColorDialog


class Canvas(QLabel):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window

        self.history = []
        self.future = []

        pixmap = QPixmap(800, 500)
        pixmap.fill(Qt.GlobalColor.white)
        self.setPixmap(pixmap)
        self.tool = "pen"

        self.last_x, self.last_y = None, None
        self.pen_color = QColor('#000000')
        self.pen_size = 4
        self.eraser = False

        self.temp_end_point = None

        self.save_state()

    def save_state(self):
        self.history.append(self.pixmap().copy())
        if len(self.history) > 20:
            self.history.pop(0)
        self.future.clear()

    def undo(self):
        if len(self.history) > 1:
            self.future.append(self.history.pop())
            self.setPixmap(self.history[-1])

    def redo(self):
        if self.future:
            self.history.append(self.future.pop())
            self.setPixmap(self.history[-1])

    def set_pen_color(self, c):
        self.pen_color = QColor(c)

    def fill_color(self, color, pos):
        pixmap = self.pixmap()
        if pixmap is None:
            print("❌ Нет pixmap!")
            return

        img = QImage(pixmap.toImage())
        if not QRect(0, 0, img.width(), img.height()).contains(pos):
            print(f"❌ Позиция вне изображения: {pos}")
            return

        target_color = img.pixelColor(pos)
        if target_color.rgba() == color.rgba():
            print("🎨 Цвет совпадает, заливка не нужна")
            return

        painter = QPainter(pixmap)
        painter.setPen(QPen(color))

        stack = [(pos.x(), pos.y())]
        checked = set()

        while stack:
            x, y = stack.pop()
            if (x, y) in checked:
                continue
            checked.add((x, y))

            if img.pixelColor(x, y).rgba() == target_color.rgba():
                painter.drawPoint(x, y)
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < img.width() and 0 <= ny < img.height():
                        stack.append((nx, ny))

        painter.end()
        self.setPixmap(pixmap)
        self.save_state()

    def clear(self):
        new_pixmap = QPixmap(self.width(), self.height())
        new_pixmap.fill(Qt.GlobalColor.white)
        self.setPixmap(new_pixmap)
        self.save_state()

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.tool in ["square", "circle", "line", "arrow"] and self.temp_end_point:
            painter = QPainter(self)
            p = painter.pen()
            p.setWidth(self.pen_size)
            p.setColor(self.pen_color)
            painter.setPen(p)

            start = QPoint(int(self.last_x), int(self.last_y))
            end = self.temp_end_point
            rect = QRect(start, end).normalized()

            if self.tool == "square":
                painter.drawRect(rect)
            elif self.tool == "circle":
                painter.drawEllipse(rect)
            elif self.tool == "line":
                painter.drawLine(start, end)
            elif self.tool == "arrow":
                painter.drawLine(start, end)
                angle = math.atan2(start.y() - end.y(), start.x() - end.x())
                arrow_size = 15
                arrow_p1 = QPoint(
                    int(end.x() + arrow_size * math.cos(angle + math.pi / 6)),
                    int(end.y() + arrow_size * math.sin(angle + math.pi / 6))
                )
                arrow_p2 = QPoint(
                    int(end.x() + arrow_size * math.cos(angle - math.pi / 6)),
                    int(end.y() + arrow_size * math.sin(angle - math.pi / 6))
                )
                painter.drawLine(end, arrow_p1)
                painter.drawLine(end, arrow_p2)

    def mouseMoveEvent(self, e) -> None:
        if self.last_x is None:
            self.last_x = e.position().x()
            self.last_y = e.position().y()
        if self.tool == "pen":
            canvas = self.pixmap()
            painter = QPainter(canvas)
            p = painter.pen()
            p.setWidth(self.pen_size)
            p.setColor(QColor("#FFFFFF") if self.eraser else self.pen_color)
            painter.setPen(p)
            painter.drawLine(int(self.last_x),
                             int(self.last_y),
                             int(e.position().x()),
                             int(e.position().y()))
            painter.end()
            self.setPixmap(canvas)
            self.last_x = e.position().x()
            self.last_y = e.position().y()
        elif self.tool in ["square", "circle", "line", "arrow"]:
            self.temp_end_point = e.position().toPoint()
            self.update()

    def mouseReleaseEvent(self, e) -> None:
        pos = e.position().toPoint()

        if self.tool == "can":
            self.fill_color(self.pen_color, pos)

        elif self.tool in ["square", "circle", "line", "arrow"]:
            canvas = self.pixmap()
            painter = QPainter(canvas)
            p = painter.pen()
            p.setWidth(self.pen_size)
            p.setColor(self.pen_color)
            painter.setPen(p)

            start = QPoint(int(self.last_x), int(self.last_y))
            end = e.position().toPoint()

            rect = QRect(start, end).normalized()

            if self.tool == "square":
                painter.drawRect(rect)
            elif self.tool == "circle":
                painter.drawEllipse(rect)
            elif self.tool == "line":
                painter.drawLine(start, end)
            elif self.tool == "arrow":
                # Рисуем основную линию стрелки
                painter.drawLine(start, end)

                # Рисуем наконечник стрелки
                angle = math.atan2(start.y() - end.y(), start.x() - end.x())
                arrow_size = 15  # Размер наконечника

                arrow_p1 = QPoint(
                    int(end.x() + arrow_size * math.cos(angle + math.pi / 6)),
                    int(end.y() + arrow_size * math.sin(angle + math.pi / 6))
                )
                arrow_p2 = QPoint(
                    int(end.x() + arrow_size * math.cos(angle - math.pi / 6)),
                    int(end.y() + arrow_size * math.sin(angle - math.pi / 6))
                )

                painter.drawLine(end, arrow_p1)
                painter.drawLine(end, arrow_p2)

            painter.end()
            self.setPixmap(canvas)
            self.save_state()

        elif self.tool == "picker":
            img = self.pixmap().toImage()
            if QRect(0, 0, img.width(), img.height()).contains(pos):
                picked_color = img.pixelColor(pos)
                hex_color = picked_color.name()

                self.main_window.set_current_color(hex_color)
                self.set_pen_color(hex_color)
                self.main_window.canvas.set_pen_color(hex_color)

                self.main_window.pen_pressed()

        elif self.tool == "text":
            text, ok = QtWidgets.QInputDialog.getText(self, "Введите текст", "Текст:")
            if ok and text:
                canvas = self.pixmap()
                painter = QPainter(canvas)
                painter.setPen(QPen(self.pen_color))
                font = painter.font()
                font.setFamily(self.main_window.fontComboBox.currentFont().family())
                font.setPointSize(int(self.main_window.fontSizeComboBox.currentText()))
                painter.setFont(font)
                painter.drawText(pos, text)
                painter.end()
                self.setPixmap(canvas)
                self.save_state()

        else:
            self.save_state()

        self.last_x, self.last_y = None, None
        self.temp_end_point = None
        self.update()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Picasso")

        # Меню "File"
        main_menu = self.menuBar()
        file_menu = main_menu.addMenu("File")

        new_img_action = QAction(QIcon('icons/new-image.png'), 'New', self)
        open_action = QAction(QIcon('icons/open-image.png'), 'Open', self)
        save_action = QAction(QIcon('icons/save-image.png'), 'Save', self)

        file_menu.addAction(new_img_action)
        file_menu.addAction(open_action)
        file_menu.addAction(save_action)
        self.setFixedSize(QSize(400, 300))

        new_img_action.triggered.connect(self.new_img)
        open_action.triggered.connect(self.open_file)
        save_action.triggered.connect(self.save_img)

        self.canvas = Canvas(self)
        w = QWidget()
        l = QVBoxLayout()
        w.setLayout(l)
        l.addWidget(self.canvas)
        self.setCentralWidget(w)

        self.setFixedSize(QSize(800, 600))
        self.current_color = "#000000"

        palette = QHBoxLayout()
        color_picker_btn = QPushButton("Выбрать цвет")
        color_picker_btn.setFixedSize(120, 30)
        color_picker_btn.clicked.connect(self.open_color_picker)
        palette.addWidget(color_picker_btn)
        l.addLayout(palette)

        # Панели инструментов
        self.toolbar = self.addToolBar("Tools")

        self.undo_action = QAction(QIcon("icons/left.png"), "Undo", self)
        self.undo_action.triggered.connect(self.canvas.undo)
        self.toolbar.addAction(self.undo_action)

        self.redo_action = QAction(QIcon("icons/right.png"), "Redo", self)
        self.redo_action.triggered.connect(self.canvas.redo)
        self.toolbar.addAction(self.redo_action)

        # Горячие клавиши
        undo_shortcut = QShortcut(QKeySequence("Ctrl+Z"), self)
        redo_shortcut = QShortcut(QKeySequence("Ctrl+Shift+Z"), self)
        undo_shortcut.activated.connect(self.canvas.undo)
        redo_shortcut.activated.connect(self.canvas.redo)

        self.fileToolbar = QToolBar(self)
        self.fileToolbar.setIconSize(QSize(16, 16))
        self.fileToolbar.setObjectName('fileToolBar')
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.fileToolbar)

        self.sliderToolbar = QtWidgets.QToolBar(self)
        self.sliderToolbar.setIconSize(QtCore.QSize(16, 16))
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.sliderToolbar)

        self.drawingToolbar = QToolBar(self)
        self.drawingToolbar.setIconSize(QSize(16, 16))
        self.drawingToolbar.setObjectName('drawingToolBar')
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.drawingToolbar)

        # Ползунок для изменения размера текста
        sizeicon = QLabel()
        sizeicon.setPixmap(QPixmap("icons/border-weight.png"))
        self.sliderToolbar.addWidget(sizeicon)

        self.sizeselect = QSlider()
        self.sizeselect.setRange(4, 15)
        self.sizeselect.setOrientation(Qt.Orientation.Horizontal)
        self.sliderToolbar.addWidget(self.sizeselect)
        self.sizeselect.valueChanged.connect(self.change_pen_size)

        # Кнопки для рисования
        self.brushButton = QPushButton()
        self.brushButton.setIcon(QIcon('icons/paint-brush.png'))
        self.brushButton.setCheckable(True)
        self.drawingToolbar.addWidget(self.brushButton)

        self.canButton = QPushButton()
        self.canButton.setIcon(QIcon('icons/paint-can.png'))
        self.canButton.setCheckable(True)
        self.drawingToolbar.addWidget(self.canButton)

        self.eraserButton = QPushButton()
        self.eraserButton.setIcon(QIcon('icons/eraser.png'))
        self.eraserButton.setCheckable(True)
        self.drawingToolbar.addWidget(self.eraserButton)

        self.pickerButton = QPushButton()
        self.pickerButton.setIcon(QIcon('icons/pipette.png'))
        self.pickerButton.setCheckable(True)
        self.drawingToolbar.addWidget(self.pickerButton)
        self.pickerButton.clicked.connect(self.picker_pressed)

        self.fontComboBox = QtWidgets.QFontComboBox()
        self.fontComboBox.setFixedWidth(150)
        self.drawingToolbar.addWidget(self.fontComboBox)

        self.fontSizeComboBox = QtWidgets.QComboBox()
        self.fontSizeComboBox.setFixedWidth(50)
        self.fontSizeComboBox.addItems([str(s) for s in range(8, 33, 2)])
        self.fontSizeComboBox.setCurrentText("16")
        self.drawingToolbar.addWidget(self.fontSizeComboBox)


        self.textButton = QPushButton()
        self.textButton.setIcon(QIcon('icons/text.png'))
        self.textButton.setCheckable(True)
        self.drawingToolbar.addWidget(self.textButton)

        self.textButton.clicked.connect(self.text_pressed)

        # ---Выпадающий список фигур---
        self.shapeComboBox = QComboBox()
        self.shapeComboBox.addItem(QIcon("icons/none.png"), "Нет")
        self.shapeComboBox.addItem(QIcon("icons/square.png"), "Квадрат")
        self.shapeComboBox.addItem(QIcon("icons/circle.png"), "Круг")
        self.shapeComboBox.addItem(QIcon("icons/line.png"), "Линия")
        self.shapeComboBox.addItem(QIcon("icons/arrow.png"), "Стрелка")

        self.drawingToolbar.addWidget(self.shapeComboBox)

        # Подключаем обработку выбора
        self.shapeComboBox.currentIndexChanged.connect(self.shape_selected)

        # Кнопки управления файлами
        self.newFileButton = QPushButton()
        self.newFileButton.setIcon(QIcon('icons/new-image.png'))
        self.fileToolbar.addWidget(self.newFileButton)
        new_shortcut = QShortcut(QKeySequence("Ctrl+N"), self)

        self.openFileButton = QPushButton()
        self.openFileButton.setIcon(QIcon('icons/open-image.png'))
        self.fileToolbar.addWidget(self.openFileButton)
        open_shortcut = QShortcut(QKeySequence("Ctrl+O"), self)

        self.saveFileButton = QPushButton()
        self.saveFileButton.setIcon(QIcon('icons/save-image.png'))
        self.fileToolbar.addWidget(self.saveFileButton)
        save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)

        self.copyFileButton = QPushButton()
        self.copyFileButton.setIcon(QIcon('icons/copy-image.png'))
        self.fileToolbar.addWidget(self.copyFileButton)

        self.openFileButton.clicked.connect(self.open_file)
        self.newFileButton.clicked.connect(self.new_img)
        self.saveFileButton.clicked.connect(self.save_img)
        self.copyFileButton.clicked.connect(self.copy_to_clipboard)

        self.canButton.clicked.connect(self.can_pressed)
        self.brushButton.clicked.connect(self.pen_pressed)
        self.eraserButton.clicked.connect(self.eraser_pressed)

        save_shortcut.activated.connect(self.save_img)
        open_shortcut.activated.connect(self.open_file)
        new_shortcut.activated.connect(self.new_img)

        self.all_buttons = [self.canButton, self.brushButton, self.eraserButton]
        self.all_buttons.append(self.pickerButton)
        self.all_buttons.append(self.textButton)

    def set_current_color(self, c):
        self.current_color = c

    def release_buttons(self, btn):
        if btn is not self.eraserButton:
            self.canvas.eraser = False
        for b in self.all_buttons:
            b.setChecked(False)
        if btn is not None:
            btn.setChecked(True)

    def open_color_picker(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.canvas.set_pen_color(color)

    def change_pen_size(self, s):
        self.canvas.pen_size = s

    def change_color(self, color):
        color_effect = QGraphicsColorizeEffect()
        color_effect.setColor(QColor(color))
        self.label.setGraphicsEffect(color_effect)

    def new_img(self):
        self.canvas.clear()

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Open file', "", "PNG images files (*.png); JPEG image files (*jpg); All files (*.*)")
        if path:
            pixmap = QPixmap()
            pixmap.load(path)

            iw, ih = pixmap.width(), pixmap.height()

            cw, ch = 800, 500

            if iw / cw < ih / ch:
                pixmap = pixmap.scaledToWidth(cw)
                hoff = (pixmap.height() - ch) // 2
                pixmap = pixmap.copy(
                    QRect(QPoint(0, hoff), QPoint(cw, pixmap.height() - hoff))
                )
            elif iw / cw > ih / ch:
                pixmap = pixmap.scaledToHeight(ch)
                woff = (pixmap.width() - cw) // 2
                pixmap = pixmap.copy(
                    QRect(QPoint(woff, 0), QPoint(pixmap.width() - woff, ch))
                )
            self.canvas.setPixmap(pixmap)

    def save_img(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save file", "", "PNG Image file (*.png)")
        if path:
            pixmap = self.canvas.pixmap()
            pixmap.save(path, "PNG")

    def can_pressed(self):
        self.release_buttons(self.canButton)
        self.canvas.tool = "can"
        self.canvas.set_pen_color(self.current_color)

    def pen_pressed(self):
        self.release_buttons(self.brushButton)
        self.canvas.tool = "pen"
        self.canvas.set_pen_color(self.current_color)

    def eraser_pressed(self):
        self.release_buttons(self.eraserButton)
        self.canvas.tool = "pen"
        self.canvas.eraser = True
        self.canvas.set_pen_color(QColor("#FFFFFF"))

    def copy_to_clipboard(self):
        clipboard = QApplication.clipboard()
        clipboard.setPixmap(self.canvas.pixmap())

    def picker_pressed(self):
        self.release_buttons(self.pickerButton)
        self.canvas.tool = "picker"

    def shape_selected(self, index):
        shapes = ["none", "square", "circle", "line", "arrow"]
        selected_shape = shapes[index]
        self.canvas.tool = selected_shape
        self.release_buttons(None)
        print(f"Выбрана фигура: {selected_shape}")

    def text_pressed(self):
        self.release_buttons(self.textButton)
        self.canvas.tool = "text"


app = QApplication(sys.argv)
app.setWindowIcon(QIcon('icons/pallete.png'))
window = MainWindow()
window.show()

app.exec()
