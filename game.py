#!/usr/bin/env python3

# The 2048 game implementation on PyQt5.
# Copyright (C) 2019  Denys Ksenchuk <denny.ks359@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.


# import standard
import sys
import random
import configparser

# import third-party
from PyQt5 import QtWidgets, QtGui, QtCore

# read configuration
cfg = configparser.ConfigParser()
cfg.read('settings.ini')


class Tile(QtCore.QObject):

    def __init__(self, matrix, value):
        super(Tile, self).__init__()
        self.matrix = matrix
        self.value = value
        self._x = 0
        self._y = 0
        self._width = 0
        self._height = 0
        self.move_animation = QtCore.QPropertyAnimation(self, b'geometry')
        self.move_animation.setDuration(int(cfg.get("Appearance", "time.animations")))
        self.spawn_animation = QtCore.QPropertyAnimation(self, b'geometry')
        self.spawn_animation.setDuration(int(cfg.get("Appearance", "time.animations")))
        self.splash_animation = QtCore.QPropertyAnimation(self, b'geometry')
        self.splash_animation.setDuration(int(cfg.get("Appearance", "time.animations")))

        self.cell_color = QtGui.QColor("#" + cfg.get("Appearance", "color.%s" % value if value <= 2048 else 2048))
        self.text_color = QtGui.QColor("#" + cfg.get("Appearance", "color.text.dark"))
        if value > 4: self.text_color = QtGui.QColor("#" + cfg.get("Appearance", "color.text.light"))
        self.pen = QtGui.QPen(QtCore.Qt.SolidLine)
        self.brush = QtGui.QBrush(self.cell_color)
        self.font = QtGui.QFont()

    def setGeometry(self, rect: QtCore.QRect):
        self._x = rect.x()
        self._y = rect.y()
        self._width = rect.width()
        self._height = rect.height()
        self.matrix.parent.update()

    def getGeometry(self):
        if int(self.matrix.tl) == int(self._width):
            return QtCore.QRect(self._x, self._y, self._width, self._height)
        else:
            return QtCore.QRect(int(self._x + (self.matrix.tl - self._width) / 2),
                                int(self._y + (self.matrix.tl - self._width) / 2),
                                self._width,
                                self._height)

    def render(self, painter):
        self.pen.setColor(self.cell_color)
        painter.setPen(self.pen)
        painter.setBrush(self.brush)
        painter.drawRoundedRect(self.getGeometry(),
                                self.matrix.sf * 3,
                                self.matrix.sf * 3,
                                QtCore.Qt.AbsoluteSize)
        self.pen.setColor(self.text_color)
        painter.setPen(self.pen)
        pixel_size = int(16 * self.matrix.sf * (self._width/self.matrix.tl))
        self.font.setPixelSize(pixel_size if pixel_size else 1)
        painter.setFont(self.font)
        painter.drawText(self.getGeometry(),
                         QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter,
                         str(self.value))

    def spawn(self):
        self.spawn_animation.setStartValue(QtCore.QRect(self._x, self._y, int(self.matrix.tl/2), int(self.matrix.tl/2)))
        self.spawn_animation.setEndValue(QtCore.QRect(self._x, self._y, self._width, self._height))
        self.spawn_animation.start()

    def splash(self):
        self.splash_animation.setStartValue(self.getGeometry())
        self.splash_animation.setKeyValueAt(0.5, QtCore.QRect(self._x, self._y,
                                                       int(self._width + 5 * self.matrix.sf),
                                                       int(self._height + 5 * self.matrix.sf)))
        self.splash_animation.setEndValue(self.getGeometry())
        self.splash_animation.start()

    def move(self, target: QtCore.QPoint):
        self.move_animation.setStartValue(self.getGeometry())
        self.move_animation.setEndValue(QtCore.QRect(target.x(), target.y(), self._width, self._height))
        self.move_animation.start()

    def __str__(self):
        return str(self.value)

    geometry = QtCore.pyqtProperty(QtCore.QRect, fset=setGeometry)


class Matrix:

    def __init__(self, parent):
        self.parent = parent                      # parent link for tiles updating
        self.data = []                            # tiles and coords massive
        self.grid = int(cfg.get("Game", "grid"))  # grid resolution
        self.sf = 1                               # current scale factor
        self.tl = 37.5                            # target tile length
        self.sp = 4                               # space beetwen tiles
        self.modified = False                     # merge anchor
        save = cfg.get("Game", "save")
        self.fill(list(map(int, save.split(" "))) if save else None)
        self.score = int(cfg.get("Game", "score"))
        self.highscore = int(cfg.get("Game", "highscore"))
        self.previous_matrix = None
        self.previous_score = 0

    def update(self):
        self.tl = (150.0 / self.grid) * self.sf       # length of tile side
        self.sp = (20.0 / (self.grid + 1)) * self.sf  # space beetwen tiles
        for row in range(self.grid):
            for cell in range(self.grid):
                self.data[row][cell]['position'] = QtCore.QPoint(int(20 * self.sf + (cell + 1) * self.sp + cell * self.tl),
                                                                 int(130 * self.sf + (row + 1) * self.sp + row * self.tl))
                if self.data[row][cell]['data'][0]:
                    self.data[row][cell]['data'][0].setGeometry(QtCore.QRect(self.data[row][cell]['position'].x(),
                                                                             self.data[row][cell]['position'].y(),
                                                                             int(self.tl),
                                                                             int(self.tl)))

    def fill(self, defaults=None):
        # create empty
        self.data = []
        for row in range(self.grid):
            self.data.append([])
            for column in range(self.grid):
                self.data[row].append({'position': None, 'data': []})
        # create source
        if defaults and len(defaults) == self.grid ** 2:
            src = defaults
        else:
            src = [0 for index in range(self.grid ** 2)]
        # fill
        counter = 0
        for row in self.data:
            for cell in row:
                cell['data'].append(Tile(self, src[counter]) if src[counter] else 0)
                counter += 1

    def to_render(self):
        res = []
        for row in self.data:
            for cell in row:
                if cell['data'][0]:
                    res.append(cell['data'][0])
                    if len(cell['data']) > 1:
                        res.append(cell['data'][1])

        return res

    def spawn(self):
        empty = []
        for row in range(self.grid):
            for cell in range(self.grid):
                if self.data[row][cell]['data'][0] == 0:
                    empty.append((row, cell))
        row, cell = random.choice(empty)
        tile = Tile(self, 4 if random.randrange(99) > 89 else 2)
        tile.setGeometry(QtCore.QRect(self.data[row][cell]['position'].x(),
                                      self.data[row][cell]['position'].y(),
                                      int(self.tl), int(self.tl)))
        self.data[row][cell]['data'] = [tile]
        tile.spawn()

    def collect(self):
        for row in self.data:
            for cell in row:
                if len(cell['data']) > 1:
                    score = cell['data'][0].value + cell['data'][1].value
                    self.score += score
                    if self.score > self.highscore:
                        self.highscore = self.score
                    new_tile = Tile(self, score)
                    new_tile.setGeometry(QtCore.QRect(cell['position'].x(),
                                                      cell['position'].y(),
                                                      int(self.tl), int(self.tl)))
                    cell['data'] = [new_tile]
                    new_tile.splash()

    def merge(self):
        self.modified = False
        for row in range(self.grid):
            for cell in range(self.grid):
                if self.data[row][cell]['data'][0]:
                    src = self.data[row][cell]['data']
                    tile = src[0]
                    target = None
                    for tc in range(cell):
                        if len(self.data[row][:cell][- tc - 1]['data']) > 1:
                            continue
                        if self.data[row][:cell][- tc - 1]['data'][0] == 0:
                            self.data[row][:cell][- tc - 1]['data'] = [src[0]]
                            target = self.data[row][:cell][- tc - 1]['position']
                            del src[0]
                            src.append(0)
                            src = self.data[row][:cell][- tc - 1]['data']
                            self.modified = True
                        elif self.data[row][:cell][- tc - 1]['data'][0].value == src[0].value:
                            self.data[row][:cell][- tc - 1]['data'].append(src[0])
                            target = self.data[row][:cell][- tc - 1]['position']
                            del src[0]
                            src.append(0)
                            src = self.data[row][:cell][- tc - 1]['data']
                            self.modified = True
                            break
                        else:
                            break
                    if target:
                        src[-1].move(target)

    def reverse(self):
        data = []
        for row in self.data:
            new_row = []
            for cell in row:
                new_row.insert(0, cell)
            data.append(new_row)
        self.data = data

    def rotateLeft(self):
        data = [[] for x in range(self.grid)]
        for row in range(self.grid):
            for cell in range(self.grid):
                data[- 1 - cell].append(self.data[row][cell])
        self.data = data

    def rotateRight(self):
        data = [[] for x in range(self.grid)]
        for row in range(self.grid):
            for cell in range(self.grid):
                data[cell].insert(0, self.data[row][cell])
        self.data = data

    def __str__(self):
        data = []
        for row in self.data:
            new_row = []
            for cell in row:
                new_row.append([str(item) for item in cell['data']])
            data.append(str(new_row))
        return "\n".join(data)


class Canvas(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(Canvas, self).__init__(parent)
        self.matrix = parent.matrix
        self.painter = QtGui.QPainter()
        self.sf = 1
        self.new_button = QtWidgets.QPushButton(cfg.get("Locale", "new"), self)
        self.new_button.setFocusPolicy(QtCore.Qt.NoFocus)
        self.new_button.clicked.connect(parent.newGame)
        self.undo_button = QtWidgets.QPushButton(cfg.get("Locale", "undo"), self)
        self.undo_button.setFocusPolicy(QtCore.Qt.NoFocus)
        self.undo_button.clicked.connect(parent.undo)

    def paintEvent(self, event):
        self.painter.begin(self)
        self.painter.setRenderHints(QtGui.QPainter.Antialiasing |
                                    QtGui.QPainter.TextAntialiasing)
        self.painter.setPen(QtGui.QColor("#" + cfg.get("Appearance", "color.text.dark")))
        font = QtGui.QFont()
        font.setPixelSize(int(self.sf * 30))
        self.painter.setFont(font)
        self.painter.drawText(int(self.sf * 20), int(self.sf * 43), cfg.get("Locale", "subtitle"))
        font.setPixelSize(int(self.sf * 9))
        self.painter.setFont(font)
        self.painter.drawText(int(self.sf * 20), int(self.sf * 70), cfg.get("Locale", "help"))

        st = " %s\n%s" % (cfg.get("Locale", "score"), self.matrix.score)
        hst = " %s\n%s" % (cfg.get("Locale", "best"), self.matrix.highscore)
        font.setPixelSize(int(self.sf * 10))
        self.painter.setFont(font)
        sbr = self.painter.boundingRect(self.geometry(), QtCore.Qt.TextWordWrap, st)
        hsbr = self.painter.boundingRect(self.geometry(), QtCore.Qt.TextWordWrap, hst)
        pen = QtGui.QPen(QtCore.Qt.SolidLine)
        pen.setColor(QtGui.QColor("#" + cfg.get("Appearance", "color.grid")))
        brush = QtGui.QBrush(QtGui.QColor("#" + cfg.get("Appearance", "color.grid")))
        sr = QtCore.QRect(int(self.sf * 180) - sbr.width() - hsbr.width() - int((15 * self.sf)),
                          int(self.sf * 20), sbr.width() + int(self.sf * 10), sbr.height() + int(self.sf * 6))
        hsr = QtCore.QRect(int(self.sf * 180) - hsbr.width(), int(self.sf * 20), hsbr.width() + int(self.sf * 10), hsbr.height() + int(self.sf * 6))
        self.painter.setPen(pen)
        self.painter.setBrush(brush)
        self.painter.drawRoundedRect(sr, int(self.sf * 3), int(self.sf * 3), QtCore.Qt.AbsoluteSize)
        self.painter.drawRoundedRect(hsr, int(self.sf * 3), int(self.sf * 3), QtCore.Qt.AbsoluteSize)
        pen.setColor(QtGui.QColor("#" + cfg.get("Appearance", "color.background")))
        self.painter.setPen(pen)
        self.painter.drawText(sr, QtCore.Qt.AlignVCenter|QtCore.Qt.AlignHCenter, st)
        self.painter.drawText(hsr, QtCore.Qt.AlignVCenter|QtCore.Qt.AlignHCenter, hst)

        pen = QtGui.QPen()
        pen.setStyle(QtCore.Qt.SolidLine)
        pen.setColor(QtGui.QColor("#" + cfg.get("Appearance", "color.grid")))
        brush = QtGui.QBrush(QtGui.QColor("#" + cfg.get("Appearance", "color.grid")))
        self.painter.setPen(pen)
        self.painter.setBrush(brush)
        self.painter.drawRoundedRect(int(self.sf * 20), int(self.sf * 130), int(self.sf * 170), int(self.sf * 170),
                                     int(self.sf * 3), int(self.sf * 3),
                                     QtCore.Qt.AbsoluteSize)
        pen.setColor(QtGui.QColor("#" + cfg.get("Appearance", "color.cell")))
        brush.setColor(QtGui.QColor("#" + cfg.get("Appearance", "color.cell")))
        self.painter.setPen(pen)
        self.painter.setBrush(brush)
        ln, sp = 150.0 / self.matrix.grid, 20.0 / (self.matrix.grid + 1)
        for y in range(self.matrix.grid):
            for x in range(self.matrix.grid):
                self.painter.drawRoundedRect(int(self.sf * (20 + (x + 1) * sp + x * ln)),
                                             int(self.sf * (130 + (y + 1) * sp + y * ln)),
                                             int(self.sf * ln),
                                             int(self.sf * ln),
                                             int(self.sf * 3), int(self.sf * 3),
                                             QtCore.Qt.AbsoluteSize)
        for tile in self.matrix.to_render():
            tile.render(self.painter)
        self.painter.end()

    def resizeEvent(self, ev):
        sf = ev.size().width() / float(cfg.get("Appearance", "min.width"))  # scale factor
        self.sf = sf
        self.matrix.sf = sf
        self.matrix.update()
        self.new_button.setGeometry(int(20 * sf), int(88 * sf), int(75 * sf), int(25 * sf))
        self.undo_button.setGeometry(int(115 * sf), int(88 * sf), int(75 * sf), int(25 * sf))
        dynamic_style = """QPushButton {
        border: 1px solid #%s;
        border-radius: %spx;
        background-color: #%s;
        font: %spx;
        color: #%s
        }""" % (cfg.get("Appearance", "color.grid"),
                int(sf * 3),
                cfg.get("Appearance", "color.grid"),
                int(sf * 10),
                cfg.get("Appearance", "color.background"))
        self.new_button.setStyleSheet(dynamic_style)
        self.undo_button.setStyleSheet(dynamic_style)


class Main(QtWidgets.QWidget):

    def __init__(self):
        super(Main, self).__init__()
        self.setMinimumSize(int(cfg.get("Appearance", "min.width")), int(cfg.get("Appearance", "min.height")))
        self.resize(int(cfg.get("Window", "width")), int(cfg.get("Window", "height")))
        center_point = QtWidgets.QDesktopWidget().availableGeometry().center()
        qtRect = self.geometry()
        qtRect.moveCenter(center_point)
        self.move(qtRect.topLeft())
        self.setWindowTitle(cfg.get("Locale", "title"))
        self.setAutoFillBackground(True)
        pallete = self.palette()
        pallete.setColor(self.backgroundRole(), QtGui.QColor("#" + cfg.get("Appearance", "color.background")))
        self.setPalette(pallete)
        self.matrix = Matrix(self)
        self.canvas = Canvas(self)
        self.show()
        self.matrix.spawn()

    def keyPressEvent(self, event):
        if not event.isAutoRepeat():
            self.matrix.previous_matrix = self.matrix.data.copy()
            self.matrix.previous_score = self.matrix.score
            if event.key() == QtCore.Qt.Key_Left:
                self.matrix.merge()
            elif event.key() == QtCore.Qt.Key_Up:
                self.matrix.rotateLeft()
                self.matrix.merge()
                self.matrix.rotateRight()
            elif event.key() == QtCore.Qt.Key_Right:
                self.matrix.reverse()
                self.matrix.merge()
                self.matrix.reverse()
            elif event.key() == QtCore.Qt.Key_Down:
                self.matrix.rotateRight()
                self.matrix.merge()
                self.matrix.rotateLeft()
            if self.matrix.modified:
                self.matrix.collect()
                self.matrix.spawn()

    def newGame(self):
        self.matrix.fill()
        self.matrix.update()
        self.matrix.score = 0
        self.update()
        self.matrix.spawn()

    def undo(self):
        if self.matrix.previous_matrix:
            self.matrix.data = self.matrix.previous_matrix
            self.matrix.score = self.matrix.previous_score
            self.matrix.update()
            self.update()

    def resizeEvent(self, event):
        ns = event.size()
        ar = float(cfg.get("Appearance", "aspect.ratio"))
        if ns.width() != event.oldSize().width():
            nw = ns.width()
            nh = int(nw / ar)
            if nh > ns.height():
                nh = ns.height()
                nw = int(nh * ar)
        else:
            nh = ns.height()
            nw = int(nh * ar)
            if nw > ns.width():
                nw = ns.width()
                nh = int(nw / ar)
        self.canvas.resize(nw, nh)
        self.canvas.move(int((self.width() - nw) / 2), int((self.height() - nh) / 2))

    def closeEvent(self, event):
        data = []
        for row in self.matrix.data:
            for cell in row:
                if cell['data'][0] == 0:
                    data.append(0)
                else:
                    data.append(cell['data'][0].value)
        cfg.set("Game", "save", " ".join(map(str, data)))
        cfg.set("Game", "score", str(self.matrix.score))
        cfg.set("Game", "highscore", str(self.matrix.highscore))
        cfg.set("Window", "width", str(self.canvas.width()))
        cfg.set("Window", "height", str(self.canvas.height()))
        with open('settings.ini', 'w') as target:
            cfg.write(target)
        event.accept()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    game = Main()
    app.exec_()
    sys.exit()