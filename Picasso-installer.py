import sys
import os

from PyQt6.QtCore import QSize, Qt, QRect, QPoint
from PyQt6.QtGui import QIcon, QAction, QColor, QPixmap, QFont, QPainter
from PyQt6.QtWidgets import QApplication, \
    QMainWindow, QPushButton, QLabel, QToolBar, \
    QSlider, QWidget, QVBoxLayout, QHBoxLayout, QFileDialog


def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


class Canvas(QLabel):
    def __init__(self):
        super().__init__()

        pixmap = QPixmap(800, 500)
        pixmap.fill(Qt.GlobalColor.white)
        self.setPixmap(pixmap)

        self.tool = 'pen'

        self.last_x, self.last_y = None, None
        self.pen_color = QColor('#000000')
        self.pen_size = 4
        self.eraser = False

    def set_pen_color(self, c):
        self.pen_color = QColor(c)

    def clear(self):
        pixmap = QPixmap(800, 500)
        pixmap.fill(Qt.GlobalColor.white)
        self.setPixmap(pixmap)

    def mouseMoveEvent(self, e):
        if self.last_x is None:
            self.last_x = e.position().x()
            self.last_y = e.position().y()
            return
        if self.tool == 'pen':
            canvas = self.pixmap()
            painter = QPainter(canvas)
            p = painter.pen()
            p.setWidth(self.pen_size)
            if self.eraser:
                p.setColor(QColor('#FFFFFF'))
            else:
                p.setColor(self.pen_color)
            painter.setPen(p)
            painter.drawLine(
                int(self.last_x),
                int(self.last_y),
                int(e.position().x()),
                int(e.position().y())
            )
            painter.end()
            self.setPixmap(canvas)
            self.last_x = e.position().x()
            self.last_y = e.position().y()

    def mouseReleaseEvent(self, e):
        if self.tool == 'can':
            canvas = self.pixmap()
            canvas.fill(QColor(self.pen_color))
            self.setPixmap(canvas)
        else:
            self.last_x = None
            self.last_y = None



COLORS = [
   '#000000', '#333333', '#666666', '#999999', '#ffffff', '#ff0000', '#ff4500',
   '#ff8c00', '#ffa500', '#ffd700', '#ffff00', '#9acd32', '#32cd32', '#008000',
   '#006400', '#00ced1', '#4682b4', '#0000ff', '#4b0082', '#8a2be2', '#9400d3',
   '#c71585', '#ff1493', '#ff69b4', '#ffc0cb', '#a52a2a', '#8b4513', '#d2691e',
   '#f4a460', '#deb887',
]


class QPaletteButton(QPushButton):
    def __init__(self, color):
        super().__init__()
        self.setFixedSize(QSize(24, 24))
        self.color = color
        self.setStyleSheet('background-color: %s' % color)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Picasso')

        main_menu = self.menuBar()
        file_menu = main_menu.addMenu('File')

        new_img_action = QAction(QIcon(resource_path('icons/new-image.png')), 'New', self)
        open_action = QAction(QIcon(resource_path('icons/open-image.png')), 'Open', self)
        save_action = QAction(QIcon(resource_path('icons/save-image.png')), 'Save', self)
        copy_action = QAction(QIcon(resource_path('icons/copy-image.png')), 'Copy', self)

        file_menu.addAction(new_img_action)
        file_menu.addAction(open_action)
        file_menu.addAction(save_action)
        file_menu.addAction(copy_action)

        self.setFixedSize(QSize(400, 300))
        self.setWindowIcon(QIcon(resource_path("icons/palette.ico")))

        self.canvas = Canvas()
        w = QWidget()
        l = QVBoxLayout()
        w.setLayout(l)
        l.addWidget(self.canvas)
        self.setCentralWidget(w)

        palette = QHBoxLayout()
        self.add_palette_buttons(palette)
        l.addLayout(palette)

        self.setFixedSize(QSize(800, 600))
        self.current_color = "#000000"

        new_img_action.triggered.connect(self.new_img)
        open_action.triggered.connect(self.open_file)
        save_action.triggered.connect(self.save_img)
        copy_action.triggered.connect(self.copy_to_clipboard)

        # Панели

        self.fileToolbar = QToolBar(self)
        self.fileToolbar.setIconSize(QSize(16, 16))
        self.fileToolbar.setObjectName("fileToolbar")
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.fileToolbar)

        self.sliderToolbar = QToolBar(self)
        self.sliderToolbar.setIconSize(QSize(16, 16))
        self.sliderToolbar.setObjectName("sliderToolbar")
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.sliderToolbar)

        self.drawingToolbar = QToolBar(self)
        self.drawingToolbar.setIconSize(QSize(16, 16))
        self.drawingToolbar.setObjectName("drawingToolbar")
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.drawingToolbar)

        # Для первой панели инструментов

        new_file_icon = QIcon()
        new_file_icon.addPixmap(QPixmap(resource_path('icons/new-image.png')))

        self.newFileButton = QPushButton()
        self.newFileButton.setIcon(new_file_icon)
        self.newFileButton.setObjectName('newFileButton')
        self.fileToolbar.addWidget(self.newFileButton)

        open_file_icon = QIcon()
        open_file_icon.addPixmap(QPixmap(resource_path('icons/open-image.png')))

        self.openFileButton = QPushButton()
        self.openFileButton.setIcon(open_file_icon)
        self.openFileButton.setObjectName('openFileButton')
        self.fileToolbar.addWidget(self.openFileButton)

        save_file_icon = QIcon()
        save_file_icon.addPixmap(QPixmap(resource_path('icons/save-image.png')))

        self.saveFileButton = QPushButton()
        self.saveFileButton.setIcon(save_file_icon)
        self.saveFileButton.setObjectName('saveFileButton')
        self.fileToolbar.addWidget(self.saveFileButton)

        copy_file_icon = QIcon()
        copy_file_icon.addPixmap(QPixmap(resource_path('icons/copy-image.png')))

        self.copyFileButton = QPushButton()
        self.copyFileButton.setIcon(copy_file_icon)
        self.copyFileButton.setObjectName('copyFileButton')
        self.fileToolbar.addWidget(self.copyFileButton)

        # Для второй
        sizeicon = QLabel()
        sizeicon.setPixmap(QPixmap(resource_path('icons/border-weight.png')))

        self.sliderToolbar.addWidget(sizeicon)
        self.sizeselect = QSlider()
        self.sizeselect.setRange(4, 30)
        self.sizeselect.setOrientation(Qt.Orientation.Horizontal)
        self.sliderToolbar.addWidget(self.sizeselect)

        self.sizeselect.valueChanged.connect(self.change_pen_size)

        # Для третьей

        # Кисть
        pen_icon = QIcon()
        pen_icon.addPixmap(QPixmap(resource_path('icons/paint-brush.png')))

        self.brushButton = QPushButton()
        self.brushButton.setIcon(pen_icon)
        self.brushButton.setCheckable(True)
        self.brushButton.setObjectName("brushButton")
        self.drawingToolbar.addWidget(self.brushButton)

        # Заливка
        can_icon = QIcon()
        can_icon.addPixmap(QPixmap(resource_path('icons/paint-can.png')))

        self.canButton = QPushButton()
        self.canButton.setIcon(can_icon)
        self.canButton.setCheckable(True)
        self.canButton.setObjectName("canButton")
        self.drawingToolbar.addWidget(self.canButton)

        # Ластик
        eraser_icon = QIcon()
        eraser_icon.addPixmap(QPixmap(resource_path('icons/eraser.png')))

        self.eraserButton = QPushButton()
        self.eraserButton.setIcon(eraser_icon)
        self.eraserButton.setCheckable(True)
        self.eraserButton.setObjectName("eraserButton")
        self.drawingToolbar.addWidget(self.eraserButton)

        self.openFileButton.clicked.connect(self.open_file)
        self.newFileButton.clicked.connect(self.new_img)
        self.saveFileButton.clicked.connect(self.save_img)
        self.copyFileButton.clicked.connect(self.copy_to_clipboard)

        self.canButton.clicked.connect(self.can_pressed)
        self.brushButton.clicked.connect(self.pen_pressed)
        self.eraserButton.clicked.connect(self.eraser_pressed)

        self.all_buttons = [self.canButton, self.brushButton, self.eraserButton]

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
            b = QPaletteButton(color)
            b.pressed.connect(lambda c=color: self.set_current_color(c))
            b.pressed.connect(lambda c=color: self.canvas.set_pen_color(self.current_color))
            layout.addWidget(b)

    def change_pen_size(self, s):
        self.canvas.pen_size = s

    def change_color(self, color):
        self.label.setStyleSheet(f'color: {color};')

    def new_img(self):
        self.canvas.clear()

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Open file', '', 'PNG image files (*.png); JPEG image files('
                                                                     '*.jpg); All files (*.*)')
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
                pixmap = pixmap. scaledToHeight(ch)
                woff = (pixmap.width() - cw) // 2
                pixmap = pixmap.copy(
                    QRect(QPoint(woff, 0), QPoint(pixmap.width() - woff, ch))
                )
            self.canvas.setPixmap(pixmap)

    def save_img(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save file", '', "PNG Image file (*.png)")
        if path:
            pixmap = self.canvas.pixmap()
            pixmap.save(path, "PNG")

    def copy_to_clipboard(self):
        clipboard = QApplication.clipboard()
        clipboard.setPixmap(self.canvas.pixmap())

    def can_pressed(self):
        self.release_buttons(self.canButton)
        self.canvas.tool = 'can'
        self.canvas.set_pen_color(self.current_color)

    def pen_pressed(self):
        self.release_buttons(self.brushButton)
        self.canvas.tool = 'pen'
        self.canvas.set_pen_color(self.current_color)

    def eraser_pressed(self):
        self.release_buttons(self.eraserButton)
        self.canvas.tool = 'pen'
        self.canvas.eraser = True
        self.canvas.set_pen_color(QColor('#FFFFFF'))


app = QApplication(sys.argv)

window = MainWindow()
window.show()

app.exec()
