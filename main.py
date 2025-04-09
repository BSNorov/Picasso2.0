import sys

from PyQt6 import QtWidgets, QtCore
from PyQt6.QtCore import QSize, Qt, QRect, QPoint
from PyQt6.QtGui import QIcon, QAction, QColor, QPixmap, QPainter, QImage, QPen
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, \
   QGraphicsColorizeEffect, QToolBar, QSlider, QWidget, QVBoxLayout, \
    QHBoxLayout, QFileDialog
from PyQt6.QtGui import QShortcut, QKeySequence


class Canvas(QLabel):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window  # ← сохраняем ссылку на MainWindow

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

    def mouseReleaseEvent(self, e) -> None:
        pos = e.position().toPoint()

        if self.tool == "can":
            self.fill_color(self.pen_color, pos)

        elif self.tool == "picker":
            img = self.pixmap().toImage()
            if QRect(0, 0, img.width(), img.height()).contains(pos):
                picked_color = img.pixelColor(pos)
                hex_color = picked_color.name()

                self.main_window.set_current_color(hex_color)
                self.set_pen_color(hex_color)
                self.main_window.canvas.set_pen_color(hex_color)

                self.main_window.pen_pressed()


        else:
            self.save_state()

        self.last_x, self.last_y = None, None


COLORS = [
   '#000000', '#333333', '#666666', '#999999', '#ffffff', '#ff0000', '#ff4500',
   '#ff8c00', '#ffa500', '#ffd700', '#ffff00', '#9acd32', '#32cd32', '#008000',
   '#006400', '#00ced1', '#4682b4', '#0000ff', '#4b0082', '#8a2be2', '#9400d3',
   '#c71585', '#ff1493', '#ff69b4', '#ffc0cb', '#a52a2a', '#8b4513', '#d2691e',
   '#f4a460', '#deb887',
]


class QPalletteButton(QPushButton):
    def __init__(self, color):
        super().__init__()
        self.setFixedSize(QSize(24, 24))
        self.color = color
        self.setStyleSheet('background-color: %s' % color)


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
        self.add_palette_buttons(palette)
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

    def set_current_color(self, c):
        self.current_color = c

    def release_buttons(self, btn):
        if btn is not self.eraserButton:
            self.canvas.eraser = False
        for b in self.all_buttons:
            b.setChecked(False)
        btn.setChecked(True)

    def add_palette_buttons(self, layout):
        for color in COLORS:
            b = QPalletteButton(color)
            b.pressed.connect(lambda c=color: self.set_current_color(c))
            b.pressed.connect(lambda c=color: self.canvas.set_pen_color(c))
            layout.addWidget(b)

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


app = QApplication(sys.argv)
app.setWindowIcon(QIcon('icons/pallete.png'))
window = MainWindow()
window.show()

app.exec()
