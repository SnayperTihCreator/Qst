from Qst.config import *
from enum import IntEnum


class PaintRole(IntEnum):
    Height = 200
    Widgets = 201

class QLWSubItem:
    def __init__(self, obj, rect):
        self.obj = obj
        if not isinstance(rect, QRect):
            if not rect:
                self.rect = obj.geometry()
            elif len(rect)==2:
                self.rect = QRect(QPoint(*rect), obj.size())
            elif len(rect)==4:
                self.rect = QRect(*rect)
        else:
            self.rect = rect
        self.obj.setGeometry(self.rect)

    def calc(self, rect):
        return QRect(QPoint(self.rect.x(), self.rect.y()+rect.y()), rect.size())

    def setParent(self, parent):
        self.obj.setParent(parent)

    def render(self, painter, opt): ...

class QLWSubItemWidget(QLWSubItem):
    def render(self, painter, opt):
        xy = self.calc(opt.rect).topLeft()
        self.obj.setGeometry(QRect(xy, self.rect.size()))
        self.obj.render(painter, xy)


class QLWSubItemLayout(QLWSubItem):
    def __init__(self, layout, rect):
        super().__init__(QWidget(), rect)
        self._base = layout
        self.obj.setLayout(self._base)

    def render(self, painter, opt):
        rect = self.calc(opt.rect)
        self.obj.setGeometry(rect)
        self.obj.render(painter, rect.topLeft())

    def addWidget(self, widg):
        self._base.addWidget(widg)

    def addLayout(self, lay):
        self._base.addLayout(lay)



class QstListWidgetItem:
    def __init__(self, height, *args):
        self.args = list(args)
        self.height = height
        self.parent = None

    def setParent(self, parent):
        self.parent = parent
        for sItem in self.args:
            sItem.setParent(parent)

    def append(self, subItem):
        self.args.append(subItem)
        subItem.setParent(self.parent)

    def appendCW(self, widget, rect):
        self.append(QLWSubItemWidget(widget, rect))

    def appendCL(self, layout, rect):
        self.append(QLWSubItemLayout(layout, rect))

    def insert(self, subItem, index=-1):
        self.args.insert(index, subItem)
        subItem.setParent(self.parent)

    def insertCW(self, widget, rect, index=-1):
        self.insert(QLWSubItemWidget(widget, rect), index)

    def insertCL(self, layout, rect, index=-1):
        self.insert(QLWSubItemLayout(layout, rect), index)

    def remove(self, subItem):
        self.args.remove(subItem)
        subItem.setParent(None)

    def removeAt(self, index=-1):
        return self.args.pop(index)

    def at(self, index):
        return self.args[index]

    def clear(self):
        for el in self.args:
            self.remove(el)


class QstListWidgetDelegate(QItemDelegate):

    def paint(self, painter, option, index):
        painter.save()
        self.drawObject(painter, option, index)
        painter.restore()


    def sizeHint(self, option, index):
        return QSize(option.rect.width(), index.data(PaintRole.Height))

    def restart(self, painter):
        painter.restore()
        painter.save()

    def drawObject(self, p, opt, i):
        p.fillRect(p.window(), p.background())
        self.drawBackground(p, opt, i)
        for sItem in i.data(PaintRole.Widgets):
            sItem.render(p, opt)

    def editorEvent(self, event, model, option, index):
        QCoreApplication.sendEvent(option.widget, event)
        return super().editorEvent(event, model, option, index)


class QstListWidgetModel(QAbstractListModel):
    def __init__(self, lst=None, parent=None):
        super().__init__(parent)
        self.lst = lst or []

    def setParentW(self, parent):
        for item in self.lst:
            item.setParent(parent)

    def rowCount(self, _index):
        return len(self.lst)

    def data(self, index, role):
        if not index.isValid() or index.row() >= len(self.lst): return
        if role == PaintRole.Widgets:
            return self.lst[index.row()].args
        elif role == PaintRole.Height:
            return self.lst[index.row()].height
        return

    def setData(self, index, value, role):
        print(role, "sData")
        self.lst[index.row()] = value

    def insertRow(self, row, parent):
        self.beginInsertRows(parent, 0, len(self.lst))
        self.lst.insert(row, parent.internalPointer())
        parent.internalPointer().setParent(self.parent())
        self.endInsertRows()
        return True

    def insertItem(self, item, index=-1):
        index = index if index >= 0 else len(self.lst) + index
        self.insertRow(index, self.createIndex(index, 1, item))

    def removeRow(self, row, parent):
        self.beginRemoveRows(parent, 0, len(self.lst))
        self.lst.pop(row).clear()
        self.endRemoveRows()
        return True

    def removeItem(self, item):
        index = self.lst.index(item)
        self.removeRow(index, self.createIndex(index, 1))

    def removeItemAt(self, index=-1):
        index = index if index >= 0 else len(self.lst) + index
        self.removeRow(index, self.createIndex(index, 1))

    def getRow(self, index=-1):
        index = index if index >= 0 else len(self.lst) + index
        return self.lst[index]


class QstListWidget(QListView):
    def __init__(self, values=None, parent=None):
        super().__init__(parent)
        self._model = QstListWidgetModel(values, self)
        self._model.setParentW(self)
        self._delegate = QstListWidgetDelegate()
        self.setItemDelegate(self._delegate)
        self.setModel(self._model)

    def addWidgets(self, heigth, *widgets, index=-1):
        self._model.insertItem(QstListWidgetItem(heigth, *[QLWSubItemWidget(*el)for el in widgets]), index)

    def addLayout(self, heigth, layout, index=-1):
        self._model.insertItem(QstListWidgetItem(heigth, QLWSubItemLayout(*layout)), index)

    def removeRow(self, index=-1):
        self._model.removeItemAt(index)

    def getRow(self, index=-1)->QstListWidgetItem:
        return self._model.getRow(index)