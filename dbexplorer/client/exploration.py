# -*- coding: utf-8 -*-
"""
.. module:: exploration
   :synopsis: Module pour la gestion d'une exploration
.. codeauthor:: pireh, amérique du nord, laurent frobert
"""

from PySide.QtCore import *
from PySide.QtGui import *
import os
import dbexplorer
import decimal
from dbexplorer.client.d3.naGraphe import NaView, NaIndividuView
from dbexplorer.client.d3.typeGraphe import TranstypageView
from dbexplorer.client.edit_join_dialog import EditJoinGroupDialog
from dbexplorer.client.where_widget import FiltersWidget
from dbexplorer.client import syntax
from dbexplorer.client.tables import TablesView
from simplejson import dumps
import simplejson as json
from customsql import CustomSQL
from croisement import QualificationModal
import functools
from dbexplorer.client.main import readFontSizefromconfig

iconPrefix = './img/'

        
class ExplorationView(QGraphicsView):
    def __init__(self, service, datasourceId, tab, parent=None):
        QGraphicsView.__init__(self, parent)
        self.tab = tab
        self.schema = {}  # schema of tables
        
        self.service = service
        self.datasourceId = datasourceId
        
        scene = QGraphicsScene(self)        
        self.setScene(scene)
        self.setAcceptDrops(True)
        scene.setItemIndexMethod(QGraphicsScene.NoIndex)
        self.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        
        scene.setBackgroundBrush(QColor(240, 240, 240))
        
        
        self.tablesItem = []  # tables on the scene
        self.joins = []  # joins on the scene
        
        # stock le nombre de fois que la table a ete utilise
        # necessaire pour associer automatiquement un alias du genre :
        # nomtable_2, nomtable_3
        self.countByTable = {}
        
        
        self.bWidgetDragging = False  # are we currently dragging a widget
        self.movingWidget = None
        self.mouseDownPosition = QPointF(0, 0)
        self.tempWidget = None
        self.tempLink = None
        
        
        oneItem = self.scene().addRect(QRectF(0.0, 0.0, 300.0, 300.0))  # inital item so sceneRect always contains QPoint(0, 0)
        self.scene().sceneRect()  # call scene rect so int calculates the rect 
        self.scene().removeItem(oneItem)
        
        
        
        self.setRenderHint(QPainter.Antialiasing)
        
        self.viewport().setMouseTracking(True)
    
        self.nextId = 1
        self.fontsize = int(readFontSizefromconfig())
        
    def getNextId(self):
        id = self.nextId 
        self.nextId = id + 1
        return id
    
    def textSizeHasChanged(self, newsize): 
        self.fontsize = newsize       
        for t in self.tablesItem:
            t.textSizeHasChanged(newsize)
        


    def addTable(self, tableName, pos): 
        if tableName in self.schema:
            tableSchema = self.schema[tableName]
        else:
            tableSchema = self.schema[tableName] = self.service.getTableSchema(self.datasourceId, tableName)
                   
        
        if tableName not in self.countByTable or self.countByTable[tableName] == 0:
            alias = None
            self.countByTable[tableName] = 1
        else:
            num = self.countByTable[tableName] + 1
            self.countByTable[tableName] = num 
            alias = '%s_%s' % (tableName, num)
        
        id = self.getNextId()
            
        t = TableItem(id, tableSchema, alias, self, self.fontsize)            
        t.setPos(self.mapToScene(pos))
        self.scene().addItem(t)
        self.tablesItem.append(t)
        self.tab.executeQuery()
        self.tab.setDirty(True)
        return t
            
    def mousePressEvent(self, ev):        
        oo = self.itemAt(ev.pos())
        if oo and isinstance(oo, ColumnItem):
            p2 = self.mapToScene(ev.pos())
            p3 = oo.mapFromScene(p2)
            if p3.x() < 20:
                return QGraphicsView.mousePressEvent(self, ev)
        # print 'mousepressEvent de ExplorationView'     
        self.mouseDownPosition = self.mapToScene(ev.pos())
        
        items = self.scene().items(QRectF(self.mouseDownPosition, QSizeF(0 , 0)).adjusted(-2, -2, 2, 2))  # , At(self.mouseDownPosition)                        
        items = [item for item in items if (isinstance(item, TableItem) or isinstance(item, ColumnItem)) and item.isVisible()]        
        activeItem = items[0] if items else None  # prend le premier element : plutot prendre celui ayant un zindex le plus haut 
        
        if not activeItem:
            self.tempWidget = None            
            self.unselectAllWidgets()
        # we clicked on a widget or on a line
        else:
            
            if isinstance(activeItem, ColumnItem):  # we have click on a handle
                if ev.button() == Qt.LeftButton:  # it is a left click so we want to start a new connection                                      
                    self.unselectAllWidgets()    
                    self.tempLink = TempLinkItem(self)                    
                    self.tempLink.setStartWidget(activeItem)                                                               
                    return QGraphicsView.mousePressEvent(self, ev)
                
            elif isinstance(activeItem, TableItem) :
                # if we clicked on a widget
                self.tempWidget = activeItem

                if ev.button() == Qt.LeftButton:
                    self.bWidgetDragging = True                    
                    if ev.modifiers() & Qt.ControlModifier:
                        activeItem.setSelected(not activeItem.isSelected())
                    elif activeItem.isSelected() == 0:
                        self.unselectAllWidgets()
                        activeItem.setSelected(True)
                        
                    for w in self.getSelectedWidgets():
                        w.savePosition()
                        # nous sauvegarderons les coordonnes initiale du move (pour le undo)
                                    
                return QGraphicsView.mousePressEvent(self, ev)                
            
            else:
                self.unselectAllWidgets()
            

        return QGraphicsView.mousePressEvent(self, ev)
    
    def mouseMoveEvent(self, ev):              
        point = self.mapToScene(ev.pos())
        if self.bWidgetDragging:            
            if not self.rect().contains(ev.pos()):  # cursor outside the window            
                return
            
            
            for item in self.getSelectedWidgets():
                newPos = item.oldPos + (point - self.mouseDownPosition)
                item.setCoords(newPos.x(), newPos.y())
            self.ensureVisible(QRectF(point, point + QPointF(1, 1)))
        elif self.tempLink:
            self.tempLink.updateLinePos(point)
            self.ensureVisible(QRectF(point, point + QPointF(1, 1)))    
        
        return QGraphicsView.mouseMoveEvent(self, ev)

    def mouseReleaseEvent(self, ev):        
        point = self.mapToScene(ev.pos())
        
        # if we are moving a widget
        if self.bWidgetDragging:
            # a t-on bouger la souris ?
                        
            moved = False
            for item in self.getSelectedWidgets():
                if item.pos() != item.oldPos:
                    moved = True
                                
            self.scene().update()
            self.bWidgetDragging = False
            
            if moved:    
                self.tab.setDirty(True)
                return            
            else:
                return QGraphicsView.mouseReleaseEvent(self, ev)
                
                
            
               
        elif self.tempLink:                        
            
            start = self.tempLink.startWidget or self.tempLink.widget
            end = self.tempLink.endWidget or self.tempLink.widget

            self.tempLink.remove()
            self.tempLink = None
            if end:
                end.linkLeaveEvent(self)
            # we must check if we have really connected some output to input
            if start and end and start != end and start.parentItem() != end.parentItem():                                                
                joinGroup = None
                joinGroupStart = start.parentItem().joinGroup
                joinGroupEnd = end.parentItem().joinGroup
                
                if joinGroupStart and joinGroupEnd and joinGroupStart == joinGroupEnd:
                    # print 'addLineInterdit cause 1'
                    return
                
                if joinGroupStart and joinGroupEnd and joinGroupStart != joinGroupEnd:                                      
                    joinGroupStart.mergeWith("join", end.parentItem(), start, end, joinGroupEnd)                                    
                elif joinGroupStart and not joinGroupEnd:
                    joinGroup = joinGroupStart
                    end.parentItem().joinGroup = joinGroup                    
                    joinGroup.addToGroup("join", end.parentItem(), start, end)
                    self.tab.setDirty(True)
                    self.tab.executeQuery()
                elif not joinGroupStart and joinGroupEnd:
                    joinGroup = joinGroupEnd
                    start.parentItem().joinGroup = joinGroup
                    joinGroup.addToGroup("join", start.parentItem(), start, end)
                    self.tab.setDirty(True)
                    self.tab.executeQuery()
                else:
                    # new JoinGroup
                    if len(self.joins) == 0:
                        joinGroup = JoinGroup(start.parentItem(), self)
                        start.parentItem().joinGroup = end.parentItem().joinGroup = joinGroup
                        joinGroup.addToGroup("join", end.parentItem(), start, end)    
                        self.joins.append(joinGroup)
                        self.tab.setDirty(True)
                        self.tab.executeQuery()
                    else:
                        print 'group de join deja existant'     
            
            self.scene().update()
            self.bWidgetDragging = False
            return QGraphicsView.mouseReleaseEvent(self, ev)       
        else:
            self.bWidgetDragging = False

            return QGraphicsView.mouseReleaseEvent(self, ev)                
                
                        
    def getSelectedWidgets(self):
        return self.scene().selectedItems()
    
    def unselectAllWidgets(self):
        for item in self.scene().items():
            item.setSelected(False)
            
    def getItemsAtPos(self, pos, itemType=None):
        if isinstance(pos, QGraphicsItem):
            items = self.scene().collidingItems(pos)
        else:
            items = self.scene().items(pos)
            
        if itemType is not None:
            items = [item for item in items if isinstance(item, itemType)]
        return items    
    
    # return number of items in "items" of type "type"
    def findItemTypeCount(self, items, Type):
        return sum([isinstance(item, Type) for item in items])

                             
    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat('application/x-dnditemdata'):            
            event.acceptProposedAction()
        else:
            event.ignore()
        
    dragMoveEvent = dragEnterEvent    
    
    def dropEvent(self, event):        
        if event.mimeData().hasFormat('application/x-dnditemdata'):
            tableName = event.mimeData().data('application/x-dnditemdata').data()
                        
            self.addTable(tableName, event.pos())
            
            event.acceptProposedAction()
        else:
            event.ignore()
            
    def loadTable(self, id, tableName, alias, pos): 
        if tableName in self.schema:
            tableSchema = self.schema[tableName]
        else:
            tableSchema = self.schema[tableName] = self.service.getTableSchema(self.datasourceId, tableName)
                               
            
        t = TableItem(id, tableSchema, alias, self, self.fontsize)            
        t.setPos(self.mapToScene(pos))
        self.scene().addItem(t)
        self.tablesItem.append(t)
        return t
        
class JoinGroup():
    def __init__(self, firstTableItem, view):
        self.view = view
        self.firstTableItem = firstTableItem
        self.links = []
    
                        
    def addToGroup(self, joinType, tableItem, start, end):  
        l = LinkItem(self.view, start, end, self.view.scene(), len(self.links) + 1, self)                
        start.addInEdge(l)
        end.addInEdge(l)  
        l.updatePainterPath()
        l.show()      
        self.links.append((joinType, tableItem, start, end, l))
    
    def mergeWith(self, joinType, tableItem, start, end, oldJoinGroup):
        self.addToGroup(joinType, tableItem, start, end)        
        
        # reaffect the current joinGroup to all 
        oldJoinGroup.firstTableItem.joinGroup = self
        for (oldjoinType, oldtableItem, oldstart, oldend, oldl) in oldJoinGroup.links :
            oldtableItem.joinGroup = self
            self.links.append((oldjoinType, oldtableItem, oldstart, oldend, oldl))
            oldl.joinGroup = self
            oldl.changeOrder(len(self.links))
            oldl.updatePainterPath()
            oldl.update()
        self.view.joins.remove(oldJoinGroup)
            
    def getJoin(self):
        j = []
        
        j.append(self.firstTableItem.id)
        
        for (joinType, tableItem, start, end, l) in self.links:
            j.append(joinType)
            j.append(tableItem.id)
            j.append(start.parentItem().id)
            j.append(start.column['name'])
            j.append(end.parentItem().id)
            j.append(end.column['name'])
            
        return j
            
            
class LinkItem(QGraphicsPathItem):
    def __init__(self, view, outWidget, inWidget, scene, order, joinGroup, *args):
        self.outWidget = outWidget
        self.inWidget = inWidget
        self.order = order
        self.joinGroup = joinGroup
        self.fontsize = view.fontsize        
        
        QGraphicsPathItem.__init__(self, None, None)        
        self.view = view
        self.setZValue(-10)
        
        self.setAcceptHoverEvents(True)      
        self.hoverState = False
        
        # this might seem unnecessary, but the pen size 20 is used for collision detection, when we want to see whether to to show the line menu or not 
        self.setPen(QPen(QColor(200, 200, 200), self.fontsize, Qt.SolidLine))
        if scene is not None:
            scene.addItem(self)
        
        self.caption = "%s=%s (%s)" % (self.outWidget.column['name'], self.inWidget.column['name'], self.order)
        self.captionItem = QGraphicsTextItem(self)         
        f = QFont()
        f.setPixelSize(self.fontsize)        
        self.captionItem.setFont(f) 
        self.captionItem.setDefaultTextColor(QColor(80, 80, 192))
        self.captionItem.setHtml("<center>%s</center>" % self.caption)
        self.captionItem.setAcceptHoverEvents(False)        
        self.captionItem.setAcceptedMouseButtons(Qt.NoButton)
    
    def hoverEnterEvent(self, event):                   
        self.hoverState = True    
        self.update()
        return QGraphicsItem.hoverEnterEvent(self, event)        
    
    def hoverLeaveEvent(self, event):        
        self.hoverState = False  
        self.update()     
        return QGraphicsItem.hoverLeaveEvent(self, event)
        
    def changeOrder(self, newOrder):
        self.order = newOrder
        self.caption = str(self.order)
        self.captionItem.setHtml("<center>%s</center>" % self.caption)
        
    def mousePressEvent(self, event):
        self.editGroupDialog()
        
        
    def remove(self):        
        self.hide()        
    
    def setNewSize(self,h):
        self.fontsize = h
        f = QFont()
        f.setPixelSize(self.fontsize)        
        self.captionItem.setFont(f)
            
    def updatePainterPath(self):        
        p1 = self.mapFromItem(self.outWidget, self.outWidget.getLinkPoint())
        p2 = self.mapFromItem(self.inWidget, self.inWidget.getLinkPoint())
        
        deltapos = self.outWidget.boundingRect().width() / 2
        deltanewpos = self.inWidget.boundingRect().width() / 2
        
        
        
        if p1.x() > p2.x():
            p1.setX(p1.x() - deltapos)
            p2.setX(p2.x() + deltanewpos)
            tmp = p1
            p1 = p2
            p2 = tmp
        else:
            p1.setX(p1.x() + deltapos)
            p2.setX(p2.x() - deltanewpos)    
        
        path = QPainterPath(p1)
        path.cubicTo(p1.x() + 30, p1.y(), p2.x() - 30, p2.y(), p2.x(), p2.y())
        
        self.setPath(path)   
        metrics = QFontMetrics(self.captionItem.font())
        oddLineOffset = -metrics.lineSpacing() / 2 * (len(self.caption.strip().splitlines()) % 2)
        mid = self.path().pointAtPercent(0.5)
        rect = self.captionItem.boundingRect()
        self.captionItem.setPos(mid + QPointF(-rect.width() / 2.0, -rect.height() / 2.0 + oddLineOffset))
             
        self.update()
        
    def shape(self):
        stroke = QPainterPathStroker()
        stroke.setWidth(self.fontsize) #10
        return stroke.createStroke(self.path())
    
    def boundingRect(self):
        rect = QGraphicsPathItem.boundingRect(self)        
        return rect

    def paint(self, painter, option, widget=None): 
        if self.hoverState:
            painter.setPen(QPen(QColor(0, 180, 0), self.fontsize, Qt.SolidLine))
        else:
            painter.setPen(QPen(QColor(180, 180, 180), self.fontsize, Qt.SolidLine))       
        painter.drawPath(self.path())
     
    def editGroupDialog(self):        
        j = EditJoinGroupDialog(self.joinGroup)
        j.raise_()
        response = j.exec_()    
        if response == QDialog.Accepted:            
            newJoinList = j.result()
            # remove the whole old joinGroup and reconstruct a new one
            self.view.joins.remove(self.joinGroup)
            self.joinGroup.firstTableItem.joinGroup = None
            for (__, tableItem, col1, col2, l) in self.joinGroup.links:
                tableItem.joinGroup = None
                col1.inEdge.remove(l)
                col2.inEdge.remove(l)
                l.remove()
            # end of remove
            
            # create new group link if newJoinList is not empty (or have only one table)
            if len(newJoinList) > 1:       
                (__, tableItem1, __, __) = newJoinList[0]
                newJoinGroup = JoinGroup(tableItem1, self.view)
                
                for i in range(len(newJoinList) - 1):
                    (joinType, tableItem, col1, col2) = newJoinList[i + 1]                
                    newJoinGroup.addToGroup(joinType, tableItem, col1, col2)
            
                self.view.joins.append(newJoinGroup)
                
            self.view.tab.setDirty(True)
            self.view.tab.executeQuery()
    
            
        
            
class TempLinkItem(QGraphicsPathItem):
    def __init__(self, view):  # todo : add the joinGroup to forbid drop on column from same joinGroup 
        QGraphicsPathItem.__init__(self, None, view.scene())
        self.setZValue(-10)        
        self.startWidget = None
        self.endWidget = None
        self.widget = None
        self.view = view
        
        self.setPen(QPen(QColor(180, 180, 180), self.view.fontsize, Qt.SolidLine))        
        
    def setStartWidget(self, widget):
        self.startWidget = widget
        
        
    def setEndWidget(self, widget):
        self.endWidget = widget
        
        
    def updateLinePos(self, newPos):
        if self.startWidget == None and self.endWidget == None:
            return
        
        
        
        deltanewpos = None
        widgets = [ widget for widget in self.view.getItemsAtPos(newPos, ColumnItem) if widget.isEnabled()]
        if widgets:
            if self.widget:
                self.widget.linkLeaveEvent(self)                 
            self.widget = widgets[0]
            self.widget.linkEnterEvent(self)                    
        else:  # aucune widget trouve
            if self.widget:  # on unhighlight l'ancienne widget eventuellement
                self.widget.linkLeaveEvent(self)  # to let the target widget highlight, to be replaced by an event                                    
                self.widget = None
            
        
        if self.startWidget:
            pos = self.mapFromItem(self.startWidget, self.startWidget.getLinkPoint())
            deltapos = self.startWidget.boundingRect().width() / 2            
        else:
            pos = self.mapFromItem(self.endWidget, self.endWidget.getLinkPoint())
            deltapos = self.endWidget.boundingRect().width() / 2            

        if self.widget not in [self.startWidget, self.endWidget]: 
            if self.startWidget == None :  # and self.widget.widgetInfo.outputs:
                newPos = self.mapFromItem(self.widget, self.widget.getLinkPoint())
                deltanewpos = self.widget.boundingRect().width() / 2
                
            elif self.endWidget == None :  # and self.widget.widgetInfo.inputs:
                newPos = self.mapFromItem(self.widget, self.widget.getLinkPoint())
                deltanewpos = self.widget.boundingRect().width() / 2
                
        
        if not deltanewpos:
            deltanewpos = 0
        
        
        
        if pos.x() > newPos.x():
            pos.setX(pos.x() - deltapos)
            newPos.setX(newPos.x() + deltanewpos)
                        
            tmp = pos
            pos = newPos
            newPos = tmp
            
        else:
            pos.setX(pos.x() + deltapos)
            newPos.setX(newPos.x() - deltanewpos)    
            
        path = QPainterPath(pos)        
        if self.startWidget != None:
            path.cubicTo(pos.x() + 30, pos.y(), newPos.x() - 30, newPos.y(), newPos.x(), newPos.y())            
        else:
            path.cubicTo(pos.x() - 30, pos.y(), newPos.x() + 30, newPos.y(), newPos.x(), newPos.y())
                
                
        self.setPath(path)

        
        
    def remove(self):
        self.hide()
        self.startWidget = None
        self.endWidget = None
        
        self.prepareGeometryChange()
        
        for child in self.childItems():
            child.hide()
            child.setParentItem(None)
            self.scene().removeItem(child)
            
        self.hide()
        self.scene().removeItem(self)

    
    
        
class Tab(QWidget):
    def __init__(self, service, datasourceId, mainWindow, startLabelIndexFiltersWidget=0, exploName='', parent=None, backupid=0):
        QWidget.__init__(self, parent)                
        self.backupId = backupid
        self.exploName = exploName
        self.mainWindow = mainWindow        
        self.dirty = True        
        self.currentPage = 1
        self.count = 0
        self.startLabelIndexFiltersWidget = startLabelIndexFiltersWidget
        
        self.service = service
        self.datasourceId = datasourceId
        self.view = ExplorationView(service, datasourceId, self)
        
        
        self.naView = NaView(self)
        self.naIndividuView = NaIndividuView(self)
        self.transtypageView = TranstypageView(self)
        
        self.stackedViews = QStackedWidget()
        self.stackedViews.addWidget(self.view)
        self.stackedViews.addWidget(self.naView)
        self.stackedViews.addWidget(self.naIndividuView)
        self.stackedViews.addWidget(self.transtypageView)
        
        self.selectedColumns = []
        self.selectedRows = []
        self.currentFilter = None
        self.add_and_filters = None
         
        
        self.executeButton = QCheckBox(_(u'Auto Execute'))      
        self.autoexecute = True
        self.executeButton.setChecked(True)
        self.executeButton.stateChanged.connect(self.changeAutoExecuteMode)
                        
        self.sceneScaleCombo = QComboBox()
        self.sceneScaleCombo.addItems(["50%", "75%", "100%", "125%", "150%"])
        self.sceneScaleCombo.setCurrentIndex(2)
        self.sceneScaleCombo.currentIndexChanged[str].connect(self.sceneScaleChanged)
        
        
        self.queryTools = FiltersWidget(self, self.startLabelIndexFiltersWidget)
                
        l = QGridLayout()
        l.addWidget(self.sceneScaleCombo, 0, 0)
        l.addWidget(self.executeButton, 1, 0)
        l.addWidget(self.queryTools, 2, 0)
        q = QWidget()
        q.setLayout(l)
        l.setContentsMargins(0, 0, 0, 0)
        
        self.lineAction = QFrame()
        self.lineAction2 = QFrame()
        
        lineActionLayout = QGridLayout()
        lineActionLayout.setContentsMargins(0, 0, 0, 0)
        
        lineActionLayout2 = QGridLayout()
        lineActionLayout2.setContentsMargins(0, 0, 0, 0)
        
        showSqlButton = QPushButton(_(u"vue SQL"))
        self.showBurtButton = QPushButton(_(u"croisement de variables"))
        self.showBurtButton.setEnabled(False)
        showCustomSQLButton = QPushButton(_(u"SQL manuel"))
        exportButton = QPushButton(_(u"export"))
        
        self.grapheExploButton = QComboBox()
        self.grapheExploButton.addItems([_(u'vue Explo'), _(u'na variable'), _(u'na individu'), _(u'transtypage')])
        self.grapheExploButton.currentIndexChanged.connect(self.showGraphe)
        
        createViewButton = QPushButton(_(u"création vue"))
        
        
        self.firstButton = QPushButton(QIcon(QPixmap(os.path.join(iconPrefix, 'db/icon_firstRecord.png'))), '')
        self.firstButton.setMaximumWidth(40)
        self.prevButton = QPushButton(QIcon(QPixmap(os.path.join(iconPrefix, 'db/icon_previousRecord.png'))), '')
        self.prevButton.setMaximumWidth(40)                
        self.nbEnreg = QLabel(_(u"enreg. - à - sur <b>-</b>"))
        self.nbEnreg.setSizePolicy(QSizePolicy.Minimum , QSizePolicy.Minimum)
        
        self.nbEnregParPage = QLineEdit('10')
        self.nbEnregParPage.setMaxLength(3)                
        self.nbEnregParPage.setSizePolicy(QSizePolicy.Minimum , QSizePolicy.Minimum)
        self.nbEnregParPage.setMaximumWidth(30)        
        self.nbEnregParPageLabel = QLabel(_(u'/ pages'))
        self.nextButton = QPushButton(QIcon(QPixmap(os.path.join(iconPrefix, 'db/icon_nextRecord.png'))), '')     
        self.nextButton.setMaximumWidth(40)    
        self.lastButton = QPushButton(QIcon(QPixmap(os.path.join(iconPrefix, 'db/icon_lastRecord.png'))), '')
        self.lastButton.setMaximumWidth(40)
        self.refreshButton = QPushButton(QIcon(QPixmap(os.path.join(iconPrefix, 'db/refresh-icon.png'))), '')
        self.refreshButton.setMaximumWidth(40)
        
        self.nbEnregParPage.setValidator(QIntValidator(self.nbEnregParPage))
        
        self.nbEnregParPage.returnPressed.connect(self.changeNbEnregPerPage)
             
        self.firstButton.clicked.connect(self.goToFirstPage)
        self.prevButton.clicked.connect(self.goToPrevPage)
        self.nextButton.clicked.connect(self.goToNextPage)
        self.lastButton.clicked.connect(self.goToLastPage)
        self.refreshButton.clicked.connect(self.refreshQuery)
        
        showSqlButton.clicked.connect(self.openHideSqlView)   
        createViewButton.clicked.connect(self.createView)
        self.showBurtButton.clicked.connect(self.openHideBurtView) 
        showCustomSQLButton.clicked.connect(self.openHideCustomSQL)
        
        exportButton.clicked.connect(self.openSaveCsv)
        
        xpos = 0     
        lineActionLayout.addWidget(showSqlButton, 0, xpos)
        xpos += 1
        lineActionLayout.addWidget(self.showBurtButton, 0, xpos)
        xpos += 1
        lineActionLayout.addWidget(showCustomSQLButton, 0, xpos)
        xpos += 1
        
        lineActionLayout.addWidget(exportButton, 0, xpos)
        xpos += 1
        
        lineActionLayout.addWidget(self.grapheExploButton, 0, xpos)
        xpos += 1        
        lineActionLayout.addWidget(createViewButton, 0, xpos)
        xpos += 1
        
        self.spacer = QSpacerItem(1, 1, hData=QSizePolicy.Expanding) 
        lineActionLayout.addItem(self.spacer, 0, xpos)
        
          
        xpos = 0
        lineActionLayout2.addWidget(self.firstButton, 0, xpos)
        xpos += 1
        lineActionLayout2.addWidget(self.prevButton, 0, xpos)
             
        xpos += 1
        lineActionLayout2.addWidget(self.nbEnreg, 0, xpos)
        
        xpos += 1
        lineActionLayout2.addWidget(self.nbEnregParPage, 0, xpos)
        
        xpos += 1
        lineActionLayout2.addWidget(self.nbEnregParPageLabel, 0, xpos)
        xpos += 1
        lineActionLayout2.addWidget(self.nextButton, 0, xpos)
        xpos += 1
        lineActionLayout2.addWidget(self.lastButton, 0, xpos)
        xpos += 1
        lineActionLayout2.addWidget(self.refreshButton, 0, xpos)
        xpos += 1
        self.spacer2 = QSpacerItem(1, 1, hData=QSizePolicy.Expanding) 
        lineActionLayout2.addItem(self.spacer2, 0, xpos)
        
        
               
        self.lineAction.setLayout(lineActionLayout)                
        self.lineAction2.setLayout(lineActionLayout2)
        
        self.sqlView = QPlainTextEdit()
        self.sqlViewIsOpen = False
        self.sqlViewPosition = None
        self.sqlView.setWindowTitle(_(u"Vue SQL"))        
        self.sqlView.setWindowFlags(Qt.WindowStaysOnTopHint) 
        
        
               
        highlight = syntax.PythonHighlighter(self.sqlView.document())
        
        self.dataList = SelectView(self)
        self.dataTools = QTreeWidget()
        
        topWidget = QWidget()
        splitterTop = QSplitter(Qt.Horizontal)
        splitterTop.addWidget(self.stackedViews)
        
        splitterTop.addWidget(q)
        
        
        splitterTop.setStretchFactor(0, 1)
        splitterTop.setStretchFactor(1, 0)
        
        splitterTop.setStretchFactor(2, 0)
        splitterTop.setSizes([200, 150])
        toplayout = QGridLayout()
        toplayout.setContentsMargins(0, 0, 0, 0)
        toplayout.addWidget(splitterTop)
        topWidget.setLayout(toplayout)
        
        b2 = QWidget()
        b2layout = QGridLayout()
        b2layout.setContentsMargins(0, 0, 0, 0)
        
        b2layout.addWidget(self.lineAction)
        b2layout.addWidget(self.lineAction2)
        b2layout.addWidget(self.dataList)  
        b2.setLayout(b2layout)
        self.b2 = b2
        
        
        bottomlayout = QGridLayout()
        bottomlayout.setContentsMargins(0, 0, 0, 0)
        
        bottomlayout.addWidget(self.b2)
        
        bottomWidget = QWidget()
        bottomWidget.setLayout(bottomlayout)
        
         
        
        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(topWidget)
        splitter.addWidget(bottomWidget)        
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([150, 100])
        
        
        
        self.tablesView = TablesView(self)
        
        self.stackedTab = QStackedWidget()                
        self.stackedTab.addWidget(splitter)
        self.stackedTab.addWidget(self.tablesView)
        
        
        globalLayout = QGridLayout()
        globalLayout.setContentsMargins(0, 0, 0, 0)
        globalLayout.addWidget(self.stackedTab)
        
        self.setLayout(globalLayout)
        self.backupTimer = QBasicTimer()
        self.backupTimer.start(1000 * 30, self)  
        self.executeQueryEnCours = False
    
    def createView(self):
        nomVue, ok = QInputDialog.getText(self, _(u"Créer une vue de l'exploration"),_(u"Nom de la vue:"),QLineEdit.Normal,_(u"nom_vue"))
        nomVue = nomVue.replace(' ','_')
        
        sql = self.sqlView.toPlainText()
        if ok:            
            errorMsg = self.service.createView(self.datasourceId,nomVue,sql) 
            if errorMsg is not None:
                msgBox = QMessageBox()
                msgBox.setText(_(u"une erreur s'est produite : %(erreur)s"%{'erreur':errorMsg}))
                msgBox.setIcon(QMessageBox.Information)
                msgBox.exec_()
            else:
                dsItem = self.mainWindow.datasourcesTree.model().getDatasourceItemById(self.datasourceId)
                self.mainWindow.datasourcesTree.model().newTable(dsItem,nomVue)     
                
            
    def textSizeHasChanged(self, newsize):
        self.view.textSizeHasChanged(newsize)        
        self.tablesView.textSizeHasChanged(newsize)    
        
        verticalHeader = self.dataList.verticalHeader()
        verticalHeader.setMinimumSectionSize (self.view.fontsize+6)
        verticalHeader.setDefaultSectionSize(self.view.fontsize+6)
        self.dataList.resizeColumnsToContents()

    def getallfield(self, tables) :
        allfield = []
        # format de sortie {'tableId':tableItem.id,'column':columnItem.column['name'],'func':other['func'],'newname':other['newname'],'group':other['group'],'order':order}
        
        # format param tables est  {'tableName':t.name,'tableAlias':t.alias,'tableTypes':tableTypes}
        
        for tableid in tables:
            
            for columnItem in self.findTableItem(tableid).columnsItem:
                
                alias = tables[tableid]['tableAlias'] 
                if alias  is not None and len(alias) > 0:
                    nomtable = alias
                else:
                    nomtable = tables[tableid]['tableName']
                    
                allfield.append({'tableId':tableid, 'column':columnItem.column['name'], 'func':'', 'newname':'%s__%s' % (nomtable, columnItem.column['name']), 'group':'', 'order':''})
        return allfield
        
    def getNaIndividuJointure(self, did, tables, joins, sc, filtre, reverse):
        # format de sc : {'tableId':tableItem.id,'column':columnItem.column['name'],'func':other['func'],'newname':other['newname'],'group':other['group'],'order':order}
        
        allField = self.getallfield(tables)        
        (maxc, resultset, primarykeyname) = self.service.getNAIndividuJointure(did, tables, joins, allField, filtre, reverse)
                        
        ar = []                
        for (key_value, c)  in resultset:
            if key_value in self.selectedRows:
                s = True
            else:
                s = False            
            ar.append(['%s %s' % (primarykeyname, key_value), (c * 1.0) / (maxc * 1.0), c, s, key_value])  # todo impacter les colonnes deja selectionne
          
        
        j = dumps(ar)
        return j
        
    def getNaJointure(self, did, tables, joins, sc, filtre, reverse):
        # format de sc : {'tableId':tableItem.id,'column':columnItem.column['name'],'func':other['func'],'newname':other['newname'],'group':other['group'],'order':order}
        
        selectedCol = []
        for col in sc:        
            tableid = col['tableId']
            alias = tables[tableid]['tableAlias'] 
            if alias  is not None and len(alias) > 0:
                nomtable = alias
            else:
                nomtable = tables[tableid]['tableName']                
            selectedCol.append('%s__%s' % (nomtable, col['column']))
        
        allField = self.getallfield(tables)
        (maxc, resultset) = self.service.getNAJointure(did, tables, joins, allField, filtre, reverse)
                        
        ar = []                
        for (f, c)  in resultset:            
            if f in selectedCol: 
                s = True
            else:
                s = False
            ar.append([f, (c * 1.0) / (maxc * 1.0), c, s])  # todo impacter les colonnes deja selectionne
          
        
        j = dumps(ar)
        return j
    
    def getNaIndividuDataset(self, reverse):
        (did, dname) = self.mainWindow.currentDatasource
        (tables, joins, sc, filtre) = self.buildQuery()                            
        datasets = []                        
        datasets.append(self.getNaIndividuJointure(did, tables, joins, sc, filtre, reverse))
        
        msg = []
        for tid in tables:
            # {'tableName':t.name,'tableAlias':t.alias,'tableTypes':tableTypes}
            alias = tables[tid]['tableAlias']
            if alias is not None and len(alias) > 0:
                msg.append(alias)
            else:
                msg.append(tables[tid]['tableName']) 
            
        return ["/".join(msg)], datasets
    
    
    
    def getNaDataset(self, reverse):
        (did, dname) = self.mainWindow.currentDatasource
        (tables, joins, sc, filtre) = self.buildQuery()                    
        
        datasets = []
                        
        datasets.append(self.getNaJointure(did, tables, joins, sc, filtre, reverse))
        
        msg = []
        for tid in tables:
            # {'tableName':t.name,'tableAlias':t.alias,'tableTypes':tableTypes}
            alias = tables[tid]['tableAlias']
            if alias is not None and len(alias) > 0:
                msg.append(alias)
            else:
                msg.append(tables[tid]['tableName']) 
            
        return ["/".join(msg)], datasets
        
    def showGraphe(self):
        index = self.grapheExploButton.currentIndex()
        
        
        if index == 0: 
            self.selectedColumns = self.selectedColumnsSave
            self.add_and_filters = None
                
            self.executeQuery()
            self.stackedViews.setCurrentIndex(0)
        elif index == 1:
            # get data for all table on the exploration
            tablesName, datasets = self.getNaDataset(True)
                
                            
            self.selectedColumnsSave = self.selectedColumns
            self.naView.render(tablesName, datasets, True)            
            self.stackedViews.setCurrentIndex(1)
        
        elif index == 2:
            # get data for all table on the exploration
            tablesName, datasets = self.getNaIndividuDataset(True)
                                            
            self.selectedColumnsSave = self.selectedColumns
            
            self.naIndividuView.render(tablesName, datasets, True)
            
            self.stackedViews.setCurrentIndex(2)
        elif index == 3:  # vue transtypage    
            self.add_and_filters = None
            self.selectedColumnsSave = self.selectedColumns        
            self.stackedViews.setCurrentIndex(3)
            self.transtypageView.render()
        
                
    def refreshQuery(self):
        self.currentPage = 1
        self.executeQuery(razLimitOffset=False, force=True)
        
    def activeButtons(self, active):
        self.firstButton.setEnabled(active)
        self.prevButton.setEnabled(active)
        self.nextButton.setEnabled(active)
        self.lastButton.setEnabled(active)
        self.refreshButton.setEnabled(active)
            
    def removeBackupFile(self):
        (did, dname) = self.mainWindow.currentDatasource
        explorationItem = self.mainWindow.datasourcesTree.getExplorationItemForTab(did, self)        
        
        path = os.path.join(self.mainWindow.backupPath, '%d_%d_%d.backup' % (self.backupId, did, explorationItem.id))
        if os.path.exists(path):
            os.remove(path)
        
            
    def timerEvent(self, event): 
        self.automaticBackup()
        
             
    def automaticBackup(self):
        if self.dirty:
            jsonData = self.toJson()
            (did, dname) = self.mainWindow.currentDatasource
            explorationItem = self.mainWindow.datasourcesTree.getExplorationItemForTab(did, self)            
            f = open(os.path.join(self.mainWindow.backupPath, '%d_%d_%d.backup' % (self.backupId, did, explorationItem.id)), 'w')
            f.write(jsonData)
            f.flush()
            f.close()
        else:
            # exploration is not modified so no backup file
            self.removeBackupFile()
                
    def changeAutoExecuteMode(self, state):
        if state == Qt.Checked:
            self.autoexecute = True
            self.executeQuery()
        else:
            self.autoexecute = False
        
                   
    def setDirty(self, isDirty):
        self.dirty = isDirty
        self.updateTabName()
            
    def setName(self, newName):
        self.exploName = newName
        self.updateTabName()
    
    def updateTabName(self):
        index = self.mainWindow.explorationsTab.indexOf(self)
        if self.dirty:
            self.mainWindow.explorationsTab.setTabText(index, '%s %s' % (self.exploName, '*'))
            self.mainWindow.saveExplorationAction.setEnabled(True)            
        else:
            self.mainWindow.explorationsTab.setTabText(index, self.exploName)
            self.mainWindow.saveExplorationAction.setEnabled(False)            
                
    def changeNbEnregPerPage(self):        
        self.currentPage = 1
        self.executeQuery(razLimitOffset=False, force=True)
        
    def goToFirstPage(self):
        self.currentPage = 1
        self.executeQuery(razLimitOffset=False, force=True)        
    
    def goToPrevPage(self):
        if self.currentPage > 1:
            self.currentPage = self.currentPage - 1
            self.executeQuery(razLimitOffset=False, force=True)
        
    
    def goToNextPage(self):
        
        countPerPage = int(self.nbEnregParPage.text())
        lastPage = self.count / countPerPage 
        if self.count % countPerPage > 0:
            lastPage += 1
        
        if self.currentPage < lastPage:
            self.currentPage = self.currentPage + 1
            self.executeQuery(razLimitOffset=False, force=True)
    
    def goToLastPage(self):
        countPerPage = int(self.nbEnregParPage.text())
        lastPage = self.count / countPerPage 
        if self.count % countPerPage > 0:
            lastPage += 1
        self.currentPage = lastPage
        self.executeQuery(razLimitOffset=False, force=True)
    
    def getLabelNbEnreg(self, count):
        if self.count:
            countPerPage = int(self.nbEnregParPage.text())
            enreg = (self.currentPage - 1) * countPerPage + 1 
            lastEnreg = enreg + countPerPage - 1
            if lastEnreg > self.count:
                lastEnreg = self.count
                
            return _(u'enreg. %(from)d à %(to)d sur <b>%(total)d</b>') % {'from':enreg, 'to' : lastEnreg, 'total':count}
        else:
            return _(u'aucun résultat')
    
    def computeLimitOffset(self):
        countPerPage = int(self.nbEnregParPage.text())
        limit = countPerPage
        offset = (self.currentPage - 1) * countPerPage 
        return (limit, offset)
    
    
    
    def setCurrentFilter(self, filterValue):        
        self.currentFilter = filterValue
        self.executeQuery()
        
    def openHideSqlView(self):
        if self.sqlView.isVisible():            
            self.sqlViewPosition = self.sqlView.saveGeometry() 
            self.sqlView.hide()
            self.sqlViewIsOpen = False
        else:            
            self.sqlView.show()
            if self.sqlViewPosition:
                self.sqlView.restoreGeometry(self.sqlViewPosition)                
            self.sqlViewIsOpen = True
    
    def openHideCustomSQL(self):
        self.customSqlView = CustomSQL(self.service, self.datasourceId, self.sqlView.toPlainText(),self.view)                                
        self.customSqlView.setModal(True)
        self.customSqlView.show()
        
                
    def openHideBurtView(self):
                  
        qualif = QualificationModal(self)
        qualif.setModal(True)        
        qualif.show()
        response = qualif.exec_()
        
        if response == QDialog.Accepted:            
            model = qualif.result()
            self.tablesView.setModel(model)
            self.stackedTab.setCurrentWidget(self.tablesView)
        
        
            
    def sceneScaleChanged(self, scale):
        newScale = int(scale[:-1]) / 100.0
        oldMatrix = self.view.matrix()
        self.view.resetMatrix()
        self.view.translate(oldMatrix.dx(), oldMatrix.dy())
        self.view.scale(newScale, newScale)
    
    def buildFilter(self, value):
        if value is None:
            return []
        
        filter = []
        operatorName = value[0]
        filter.append(operatorName)        
        
        for index in range(1, len(value)):
            c = value[index]                        
            if c[0] == 'ET' or c[0] == 'OU':
                filter.append(self.buildFilter(c))                                                
            else:                
                (leftClause, operatorClause, rightClause, options) = c
                leftTableId = leftClause.parentItem().id 
                leftColumnName = leftClause.column['name']
                operatorId = operatorClause[0]
                
                if isinstance(rightClause, str) or isinstance(rightClause, unicode) or isinstance(rightClause, decimal.Decimal):
                    rightTableId = -1
                    rightColumnName = rightClause 
                else:
                    if rightClause:
                        rightTableId = rightClause.parentItem().id
                        rightColumnName = rightClause.column['name'] 
                    else:
                        rightTableId = None
                        rightColumnName = None
                
                filter.append([leftTableId, leftColumnName, operatorId, rightTableId, rightColumnName, options])
        return filter
    
    def decodeFilter(self, value):
        filter = []
        if value is None or len(value) == 0:
            return []
        operatorName = value[0]
        filter.append(operatorName)       
        
        for index in xrange(1, len(value)):            
            c = value[index]                        
            if c[0] == 'ET' or c[0] == 'OU':
                filter.append(self.decodeFilter(c))                                                
            else:                
                try :
                    [leftTableId, leftColumnName, operatorId, rightTableId, rightColumnName, options] = c
                except:
                    [leftTableId, leftColumnName, operatorId, rightTableId, rightColumnName] = c
                    options = {}
                
                leftClause = self.findColumnItem(leftTableId, leftColumnName)
                
                operatorClause = self.findOperatorByID(leftClause, operatorId)
                
                if rightTableId == None and rightColumnName == None:
                    rightClause = None
                elif rightTableId == -1:  # text value so no tableId
                    try:
                        value2 = decimal.Decimal(rightColumnName)
                    except:
                        value2 = rightColumnName
                    rightClause = value2
                else:
                    rightClause = self.findColumnItem(rightTableId, rightColumnName)
                    
                filter.append((leftClause, operatorClause, rightClause, options))
                              
        return filter
    
    def findOperatorByID(self, columnItem, operatorId):
        # todo : find the operator for the type of this columnItem 
        # ask to the where_widget        
        return (operatorId, '--')  # for now
    
    def findTableItemByNameOrAlias(self, nom):        
        # recherche des par alias en premier
        for t in self.view.tablesItem:
            if t.alias == nom:
                return t
        
        # si pas trouve alors on recherche par le nom de la table
        for t in self.view.tablesItem:
            if t.name == nom:
                return t
            
            
        return None
    
    def findTableItem(self, tableId):
        for t in self.view.tablesItem:
            if t.id == tableId:
                return t
        
        return None
            
        
    def findColumnItem(self, tableId, columnName):
        tableItem = self.findTableItem(tableId)
            
        if not tableItem:
            print 'findColumnItem, tableItem not found for tableId ', tableId
            return None
        
        for c in tableItem.columnsItem:
            if c.column['name'] == columnName:
                return c
            
        print 'findColumnItem, columnItem not found for tableId and columnName ', tableId, columnName
        return None
        
        
        
    def buildQuery(self):
        joins = []
        
        # construction of joinslist
        for l in self.view.joins:
            joins.append(l.getJoin())
        
        tables = {}
        for t in self.view.tablesItem:
            # print t.id,t.name,t.alias
            tableTypes = {}
            for col in t.columnsItem:
                tableTypes[col.column['name']] = (col.column['typenatif'], col.column['type'])
                
            tables[t.id] = {'tableName':t.name, 'tableAlias':t.alias, 'tableTypes':tableTypes}
        
        
        sc = []
        
        for c in self.selectedColumns:            
            (tableItem, columnItem, other) = c
            if other['order']:
                (o, t) = other['order']  # (ordre,tri)
                order = [o, t]
            else:
                order = ''
            sc.append({'tableId':tableItem.id, 'column':columnItem.column['name'], 'func':other['func'], 'newname':other['newname'], 'group':other['group'], 'order':order})    
        
        filtre = None
        if self.currentFilter:
            filtre = self.buildFilter(self.currentFilter)
            
        return (tables, joins, sc, filtre)  
    
    
    def openSaveCsv(self):
        
        fileName, filtr = QFileDialog.getSaveFileName(self, _(u"Exportation"), _(u'monexport.csv'), _("All Files (*);;Text Files (*.txt)"))
    
        if fileName:
            (tables, joins, sc, filtre) = self.buildQuery() 
            add_and_filter = self.add_and_filters
            if add_and_filter is not None: 
                if filtre is not None:
                    if filtre[0] == '??':
                        add_and_filter.append(filtre[1])
                    else:
                        add_and_filter.append(filtre) 
                
            newfilter = add_and_filter or filtre
                               
            self.service.getCsv(self.datasourceId, tables, joins, sc, newfilter, fileName)
    
    
                                      
    def executeQuery(self, razLimitOffset=True, force=False):
        add_and_filter = self.add_and_filters
        if self.executeQueryEnCours == True:
            return
        try :
            self.executeQueryEnCours = True
            if not self.autoexecute and not force:
                return
            self.activeButtons(False)
            (tables, joins, sc, filtre) = self.buildQuery()  
            if razLimitOffset:
                self.currentPage = 1            
            
            (limit, offset) = self.computeLimitOffset()   
            
            if add_and_filter is not None: 
                if filtre is not None:
                    if filtre[0] == '??':
                        add_and_filter.append(filtre[1])
                    else:
                        add_and_filter.append(filtre) 
                
            newfilter = add_and_filter or filtre        
            response = self.service.executeQuery(self.datasourceId, tables, joins, sc, newfilter, limit, offset)
            
            
                     
            if response['error'] is not None:
                self.errorMessageDialog = QErrorMessage(self)               
                 
                self.errorMessageDialog.showMessage(response['error'])
                return
                
            
            self.count = response['count']
            self.nbEnreg.setText(self.getLabelNbEnreg(response['count']))
            
            sql = response['query']
            # print "sql query response ",sql
            sql = sql.replace('SELECT', 'SELECT\n').replace('JOIN', '\nJOIN').replace(' ON ', '\n    ON ')
            sql = sql.replace(',', ',\n').replace('WHERE', 'WHERE\n').replace("LEFT OUTER", "\nLEFT OUTER")
            sql = sql.replace("GROUP BY", "\nGROUP BY").replace("ORDER BY", "\nORDER BY")
            
            self.sqlView.setPlainText(sql)
            
            resultset = response['resultset']
            
            self.dataList.close()
                
            self.dataList = SelectView(self) 
            self.b2.layout().addWidget(self.dataList)
            
            self.dataList.horizontalHeader().initializeSections()
            
            
            if len(resultset) > 0 and len(resultset[0]) > 0 and len(self.selectedColumns) > 1:
                self.showBurtButton.setEnabled(True)
            else:
                self.showBurtButton.setEnabled(False)        
                    
            if len(resultset) > 0:
                self.dataList.setRowCount(len(resultset) + 4)
                self.dataList.setColumnCount(len(resultset[0]))
                
                
                if self.selectedColumns:
                    names = []
                    for (tableItem, columnItem, other) in self.selectedColumns:
                        names.append(columnItem.column['name'])
                else:
                    names = response['header']
                self.dataList.setHorizontalHeaderLabels(names) 
                # add function line
                r = 0
                # ligne des fonctions
                
                
                self.dataList.setVerticalHeaderItem(r, QTableWidgetItem(_(u"fonction")))
                for c in range(len(resultset[0])):
                    if len(self.selectedColumns) > 0:
                        (tableItem, columnItem, other) = self.selectedColumns[c]                                        
                        combo = QComboBox()
                        model = self.getSQLFunctionForType(columnItem.column['type'])
                        if model:
                            combo.addItems(model)                                            
                            combo.setCurrentIndex(model.index(other['func']))
                            
                            func = functools.partial(self.columnFunctionChanged, combo, c)                       
                            
                            combo.currentIndexChanged.connect(func)                    
                            qindex = self.dataList.model().index(r, c, QModelIndex())
                            self.dataList.setIndexWidget(qindex, combo)
                        else:
                            newItem = QTableWidgetItem(_(u'N/A')) 
                            self.dataList.setItem(r, c, newItem)
                    else:
                        newItem = QTableWidgetItem(_(u'N/A'))
                        self.dataList.setItem(r, c, newItem)
                   
                
                r = r + 1
                # ligne des nouveaux noms
                self.dataList.setVerticalHeaderItem(r, QTableWidgetItem(_(u"nom")))
                for c in range(len(resultset[0])):
                    if len(self.selectedColumns) > 0:
                        (tableItem, columnItem, other) = self.selectedColumns[c]
                        text = QLineEdit(other['newname']) 
                        func2 = functools.partial(self.columnNameChanged, text, c)                    
                        text.editingFinished.connect(func2)                                     
                        qindex = self.dataList.model().index(r, c, QModelIndex())
                        self.dataList.setIndexWidget(qindex, text)
                        
                    else:
                        newItem = QTableWidgetItem(_(u"N/A")) 
                        self.dataList.setItem(r, c, newItem)
                
                
                r = r + 1
                # ligne des nouveaux noms
                self.dataList.setVerticalHeaderItem(r, QTableWidgetItem(_(u"groupe")))
                for c in range(len(resultset[0])):
                    if len(self.selectedColumns) > 0:
                        (tableItem, columnItem, other) = self.selectedColumns[c]
                        text = QLineEdit(other['group']) 
                        func2 = functools.partial(self.columnGroupChanged, text, c)                    
                        text.editingFinished.connect(func2)                                     
                        qindex = self.dataList.model().index(r, c, QModelIndex())
                        self.dataList.setIndexWidget(qindex, text)
                        
                    else:
                        newItem = QTableWidgetItem(_(u"N/A")) 
                        self.dataList.setItem(r, c, newItem)
                
                r = r + 1
                # ligne des nouveaux noms
                self.dataList.setVerticalHeaderItem(r, QTableWidgetItem(_(u"ordre")))
                for c in range(len(resultset[0])):
                    if len(self.selectedColumns) > 0:
                        (tableItem, columnItem, other) = self.selectedColumns[c]
                        editor = OrderEditor(other['order']) 
                        func2 = functools.partial(self.columnOrderChanged, editor, c)                    
                        editor.editingFinished.connect(func2)                                     
                        qindex = self.dataList.model().index(r, c, QModelIndex())
                        self.dataList.setIndexWidget(qindex, editor)
                        
                    else:
                        newItem = QTableWidgetItem(_(u"N/A")) 
                        self.dataList.setItem(r, c, newItem)
                
                
                r = r + 1
                countPerPage = int(self.nbEnregParPage.text())
                enreg = (self.currentPage - 1) * countPerPage + 1
                for row in resultset :                
                    self.dataList.setVerticalHeaderItem(r, QTableWidgetItem("%s" % (enreg)))
                    c = 0 
                    for column in row : 
                        if isinstance(column, decimal.Decimal):
                            newItem = QTableWidgetItem("%g" % (column))
                        else:    
                            newItem = QTableWidgetItem(column)
                        newItem.setFlags(~Qt.ItemIsEditable)
                        self.dataList.setItem(r, c, newItem)
                        c += 1
                    enreg = enreg + 1
                    r = r + 1
                    
                    
                
                
            self.activeButtons(True)
            
            verticalHeader = self.dataList.verticalHeader()
            verticalHeader.setMinimumSectionSize (self.view.fontsize+6)
            verticalHeader.setDefaultSectionSize(self.view.fontsize+6)
            self.dataList.resizeColumnsToContents()
                           
        finally:
            self.executeQueryEnCours = False
                            
    def columnNameChanged(self, textEdit, columnIndex):
        (tableItem, columnItem, other) = self.selectedColumns[columnIndex]
        
        
        if not textEdit.text() and other['func']:
            textEdit.setText(other['newname'])                                    
            msgBox = QMessageBox()
            msgBox.setText(_(u"Le nom est obligatoire quand on utilise une fonction"))
            msgBox.setIcon(QMessageBox.Information)
            msgBox.exec_()

            
            
        elif other['newname'] == textEdit.text():
            pass
        else:                                    
            other['newname'] = textEdit.text()
            self.setDirty(True)
            self.executeQuery()
        
    def columnGroupChanged(self, textEdit, columnIndex):
        (tableItem, columnItem, other) = self.selectedColumns[columnIndex]
        
        if other['group'] == textEdit.text():
            pass
        else:                                    
            other['group'] = textEdit.text()
            self.setDirty(True)
            self.executeQuery()

    def columnOrderChanged(self, editor, columnIndex):        
        (tableItem, columnItem, other) = self.selectedColumns[columnIndex]
        
        if other['order'] == editor.result():  # no modification
            pass
        elif len(editor.result()[0]) > 0:  # at least one car in the order field                                
            other['order'] = editor.result()
            self.setDirty(True)
            self.executeQuery()
        else:
            other['order'] = None
            self.setDirty(True)
            self.executeQuery()
            
    def columnFunctionChanged(self, combo, columnIndex, value):        
        (tableItem, columnItem, other) = self.selectedColumns[columnIndex]
        other['func'] = combo.currentText()  
        if not other['newname']:
            other['newname'] = '%s_%s' % (columnItem.column['name'], columnIndex)  # attention si column index change lors d'un move alors l'index peut prendre un index d�j� existant
        self.setDirty(True)     
        self.executeQuery()  
                
    def changeColumnSelected(self, tableItem, columnItem):        
        if columnItem.isInSelect and not any(t[0] == tableItem and t[1] == columnItem for t in self.selectedColumns):
            
            self.selectedColumns.append((tableItem, columnItem, {'func':'', 'newname':'', 'group':'', 'order':None}))
            self.setDirty(True)
            self.executeQuery()
        elif not columnItem.isInSelect and any(t[0] == tableItem and t[1] == columnItem for t in self.selectedColumns):
            # find element
            found = [t for t in self.selectedColumns if t[0] == tableItem and t[1] == columnItem]
            for element in found:
                self.selectedColumns.remove(element)
            self.setDirty(True)        
            self.executeQuery()
            
        
            
    def getSQLFunctionForType(self, type): 
            if type == 'STR':
                return ['', 'count', 'lower', 'upper']
            elif type == 'INT' or type == 'DEC':
                return ['', 'count', 'avg', 'min', 'max', 'sum']
            else :
                return None
    
    def toJson(self):
        joins = []
        
        # construction of joinslist
        for l in self.view.joins:
            joins.append(l.getJoin())
        
        tables = []
        for t in self.view.tablesItem:
            # print t.id,t.name,t.alias
            tableTypes = {}
            for col in t.columnsItem:
                tableTypes[col.column['name']] = (col.column['typenatif'], col.column['type'])
                
            tables.append({'id':t.id, 'tableName':t.name, 'tableAlias':t.alias, 'posx':t.pos().x(), 'posy':t.pos().y(), 'tableTypes':tableTypes})
        
        
        sc = []
        
        for c in self.selectedColumns:            
            (tableItem, columnItem, other) = c
            if other['order']:
                (o, t) = other['order']  # (ordre,tri) 
                order = [o, t]  # transformation sous forme de tableau au lieu de tuple
            else:
                order = ''
            sc.append({'tableId':tableItem.id, 'column':columnItem.column['name'], 'func':other['func'], 'newname':other['newname'], 'group':other['group'], 'order':order})    
        
        filtres = []        
        for c in self.queryTools.whereList.model().filters : 
            (thefilter, name) = c
            if thefilter == []:
                continue            
            filterDecoded = self.buildFilter(thefilter)
            if filterDecoded == []:
                continue
            filtres.append({'name':name, 'filter':filterDecoded})
        
        obj = {}
        obj['countByTable'] = self.view.countByTable
        obj['nextId'] = self.view.nextId
        obj['tables'] = tables
        obj['joins'] = joins
        obj['sc'] = sc
        obj['filtres'] = filtres
        obj['startLabelIndexFiltersWidget'] = self.queryTools.startLabelIndex
        
        # ne pas mettre apr�s
        (did, dname) = self.mainWindow.currentDatasource
        
        
        obj['exploName'] = self.exploName
        
        
        jsonData = json.dumps(obj, indent=4, use_decimal=True)
        
        return jsonData
        
        
        
    
    

class OrderEditor(QWidget):
    editingFinished = Signal()
    def __init__(self, defaultValue, parent=None):
        QWidget.__init__(self, parent=parent)
        self.setContentsMargins(0, 0, 0, 0)
        if defaultValue:
            (o, t) = defaultValue
        else:
            o = ''
            t = ''
            
        self.order = QLineEdit(o)
        self.order.setMaximumWidth(40)
        self.orderType = QComboBox()
        self.model = ['', 'ASC', 'DESC']
        self.orderType.addItems(self.model)                                            
        self.orderType.setCurrentIndex(self.model.index(t))
        self.orderType.currentIndexChanged.connect(self.modified)                        
        layout = QGridLayout()
        layout.addWidget(self.order, 0, 0)
        layout.addWidget(self.orderType, 0, 1)
        layout.setColumnStretch(2, 1)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
                        
        self.order.editingFinished.connect(self.modified)
        
    def result(self):
        o = self.order.text()
        ti = self.orderType.currentIndex()
        t = self.model[ti]
        return (o, t)
    
    def modified(self):        
        self.editingFinished.emit()
        
class SelectView(QTableWidget):
    def __init__(self, tab, parent=None):
        QTableWidget.__init__(self, parent)
        self.tab = tab
        
        horizontalHeader = self.horizontalHeader()
        if len(self.tab.selectedColumns) > 0:
            self.horizontalHeader().setMovable(True)            
        else:
            self.horizontalHeader().setMovable(False)
        
        
        horizontalHeader.sectionMoved.connect(self.columHasBeenMoved)        
        horizontalHeader.setDefaultAlignment(Qt.AlignLeft)        
        hdr = self.horizontalHeader()
        hdr.setContextMenuPolicy(Qt.CustomContextMenu)
        hdr.customContextMenuRequested.connect(self.contextMenuEvent)
        self.setWordWrap(False) 

    def contextMenuEvent(self, point):
        menu = QMenu()
        removeColumn = menu.addAction(_(u"Supprimer la colonne"))
        duplicateColumn = menu.addAction(_(u"Dupliquer la colonne")) 
        statColumn = None
        if len(self.tab.selectedColumns) > 0:
            statColumn = menu.addAction(_(u"Affiche Stat"))
                
        selectedAction = menu.exec_(self.mapToGlobal(point))
        if len(self.tab.selectedColumns) > 0 and selectedAction == statColumn:
            index = self.indexAt(point)              
            self.showDetailColumnAtIndex(index.column())
                        
        elif selectedAction == duplicateColumn:                                
            index = self.indexAt(point)        
            (tableItem, columnItem, __) = self.tab.selectedColumns[index.column()]
            newname = '%s_%s' % (columnItem.column['name'], len(self.tab.selectedColumns)) 
            self.tab.selectedColumns.append((tableItem, columnItem, {'func':'', 'newname':newname, 'group':'', 'order':None}))
            self.tab.setDirty(True)
            self.tab.executeQuery()
        elif selectedAction == removeColumn:
            index = self.indexAt(point)        
            
                        
            (tableItem, columnItem, __) = self.tab.selectedColumns.pop(index.column())
            
            # is there another same column    
            found = [t for t in self.tab.selectedColumns if t[0] == tableItem and t[1] == columnItem]    
            if not found:  # no so unselect in table view    
                columnItem.isInSelect = False    
                columnItem.preventCheckStateChanged = True
                columnItem.check.setChecked(False)
                columnItem.preventCheckStateChanged = False
                
            self.tab.setDirty(True)
            self.tab.executeQuery()
            
    def showDetailColumnAtIndex(self, index):                
        (tables, joins, sc, filtre) = self.tab.buildQuery()
        columnDetail = self.tab.service.getColumnDetailsFromQuery(self.tab.datasourceId, tables, joins, sc, filtre, index)
        type = columnDetail['type']
        
                    
        if type == 'INT' or type == 'DEC':
            self.dialog = ColumDetailDialogNumeric(columnDetail, None, None)
        elif type == 'DATE' or type == 'DATETIME':
            self.dialog = ColumDetailDialogDate(columnDetail, None, None)    
        else :
            self.dialog = ColumDetailDialog(columnDetail, None, None)
                        
               
        self.dialog.show()
        self.dialog.raise_()
        self.dialog.activateWindow()
        
        self.dialog.exec_()
              
    def columHasBeenMoved(self, logicalIndex, oldVisualIndex, newVisualIndex):
        
        # attention : si nous sommes dans le mode : non auto execute
        # les colonnes sont changées d'ordre (même dans le selectedColumns) mais les index utilis�s par
        # les fonctions partielles eux ne sont pas changé donc ils ne vont pas modifi� les bonnes colonnes
        
        self.tab.selectedColumns.insert(newVisualIndex, self.tab.selectedColumns.pop(oldVisualIndex))
        self.tab.setDirty(True)
        self.tab.executeQuery() 
                
        
        
            
class CloseButton(QGraphicsItem):
    def __init__(self, x, y, h, parent=None, *args):
        QGraphicsItem.__init__(self, scene=None, parent=parent, *args)
        self.closeIcon = QPixmap(os.path.join(iconPrefix, 'small-close-button.png'))
        if h <= 17:
            self.closeIcon = self.closeIcon.scaledToHeight(h - 2)
            
        self.setCursor(Qt.ArrowCursor)
        self.parent = parent        
        self.x = x
        self.y = y
        
    def boundingRect(self):
        return QRectF(self.x, self.y, self.x + self.closeIcon.width(), self.y + self.closeIcon.height())
        
    def newScale(self, x, y, h):
        self.x = x
        self.y = y
        self.closeIcon = QPixmap(os.path.join(iconPrefix, 'small-close-button.png'))
        if h <= 17:
            self.closeIcon = self.closeIcon.scaledToHeight(h - 2)
        
                
    def paint(self, painter, option, widget):        
        painter.drawPixmap(self.x, self.y, self.closeIcon)
        
    def mousePressEvent(self, event):        
        if event.pos().x() > self.x and event.pos().x() < (self.x + 16):
            self.parent.deleteTable() 
    
    
        
class TableItem(QGraphicsItem):
    def __init__(self, id, tableSchema, alias, view, fontsize, *args):
        QGraphicsItem.__init__(self, scene=None, *args)
        self.view = view
        self.id = id      
        self.joinGroup = None        
        font = QFont()
        # font.setPixelSize(16)
        font.setBold(True)        
        
        self.font = font
        self.name = tableSchema['tableName']
        self.tableSchema = tableSchema
        self.alias = alias
        if self.alias :
            self.text = "%s (%d)" % (self.alias, self.tableSchema['count'])
        else:
            self.text = "%s (%d)" % (self.name, self.tableSchema['count'])
        
                
        (w, h) = self.computeTextWidth (fontsize)       
        self.rect = QRectF(0, 0, w, h)
        self.setCursor(Qt.OpenHandCursor)
        self.setFlags(QGraphicsItem.ItemIsSelectable)
        
        self.columnsItem = []
        lasty = self.rect.height()
        maxWidth = self.rect.width()        
        for c in tableSchema['cols']:
            col = ColumnItem(c, fontsize, parent=self)            
            col.setPos(0, lasty)
            self.columnsItem.append(col)            
            lasty += col.boundingRect().height()
            if col.boundingRect().width() > maxWidth:
                maxWidth = col.boundingRect().width()

        self.setWidth(maxWidth)     
                       
        for col in self.columnsItem:            
            col.setWidth(maxWidth)        
            
        self.oldPos = self.pos()
        self.bounding = QRectF(0, 0, 0, 0)
        self.computeBounding()
        self.closeIcon = CloseButton(self.boundingRect().width() - h, 2, h, parent=self)

        
        
            
    def addToJoinGroup(self, joinGroup):
        self.joinGroup = joinGroup
            
    def computeBounding(self):
        r = self.rect
        for c in self.columnsItem:            
            r = r.united(c.boundingRect())
                        
            
        self.bounding = r
        
    def setPos(self, *args):
        QGraphicsItem.setPos(self, *args)
        
        for col in self.columnsItem:
            for edge in col.inEdge:
                edge.updatePainterPath()
                
    def savePosition(self):
        self.oldPos = self.pos()
        
    def restorePosition(self):
        self.setPos(self.oldPos)

    def setCoords(self, x, y):
        self.setPos(x, y)
    
    
                         
    def setWidth(self, w):
        self.rect.setWidth(w)
            
    def computeTextWidth(self, sizefont):        
        # fm = QFontMetrics(self.font)
        f = QFont()
        f.setPixelSize(sizefont)        
        fm = QFontMetrics(f)
        
        textWidthInPixels = fm.width(self.text)
        textHeightInPixels = fm.height()  
        return textWidthInPixels, textHeightInPixels
    
    def textSizeHasChanged(self, newsize):
        (w, h) = self.computeTextWidth (newsize)        
        self.rect = QRectF(0, 0, w, h)
        lasty = self.rect.height()
        maxWidth = self.rect.width()        
        for col in self.columnsItem:
            col.textSizeHasChanged(newsize)                        
            col.setPos(0, lasty)                        
            lasty += col.boundingRect().height()
            if col.boundingRect().width() > maxWidth:
                maxWidth = col.boundingRect().width()

        self.setWidth(maxWidth)     
                       
        for col in self.columnsItem:            
            col.setWidth(maxWidth)        
            
        self.oldPos = self.pos()
        self.bounding = QRectF(0, 0, 0, 0)
        self.computeBounding()
        self.closeIcon.newScale(self.boundingRect().width() - h, 2, h)
        
        #replacement des liens de jointures
        for col in self.columnsItem:
            for edge in col.inEdge:
                edge.setNewSize(newsize)
                edge.updatePainterPath()
                        
    def boundingRect(self):         
        return self.bounding
    
    def paint(self, painter, option, widget):
        
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(Qt.darkGray))
        
        painter.drawRoundedRect(self.boundingRect(), 10, 10)
        painter.fillRect(self.boundingRect().adjusted(0, self.boundingRect().height() / 2.0, 0, self.boundingRect().height() / 2.0), Qt.darkGray)
        painter.setFont(self.font)
        painter.setPen(QPen(Qt.black))        
        painter.drawText(self.rect, Qt.AlignCenter, unicode(self.text))
        
        
        
    def contextMenuEvent(self, event):        
        menu = QMenu()
        delOperator = menu.addAction(_(u"enlever la table de l'exploration"))
        selectedAction = menu.exec_(event.screenPos())
        if selectedAction == delOperator:                                
            self.deleteTable()                
            
    def transtypage(self):        
        from d3.typeGraphe import TypageView
        cols = []
        for c in self.columnsItem:
            col = []
            col.append(c.column['name'])
            col.append(c.column['typenatif'])
            col.append(c.column['type'])
            col.append(c.column['count'])
            cols.append(col)
            
        self.typeview = TypageView(self.view.tab, self)
        self.typeview.render(self.name, cols)
        
        self.view.tab.stackedViews.addWidget(self.typeview)
        self.view.tab.stackedViews.setCurrentWidget(self.typeview)
        
    def mouseReleaseEvent(self, event):
        pass
        
    
                        
    def deleteTable(self):
        isInJoin = False
        isInSelect = False
        isInFilter = False
        
        if self.joinGroup:
            isInJoin = True
        
        for c in self.view.tab.selectedColumns:            
            (tableItem, __, __) = c
            if tableItem == self:
                isInSelect = True
        
        for c in self.view.tab.queryTools.whereList.model().filters : 
            (filter, __) = c
            if self.isInFilter(filter):
                isInFilter = True
                break
        
        msg = []    
        if isInJoin:
            msg.append(_(u"cette table est utilisée dans une jointure"))
        
        if isInSelect:
            
            s = _(u"cette table est utilisée dans la sélection")
            
            msg.append(s)
            
        if isInFilter:
            msg.append(_(u"cette table est utilisée dans les filtres"))    
            
        if msg:
            msg.append('')
            msg.append(_(u"veuillez supprimer les dépendances avant d'enlever la table"))
            msgBox = QMessageBox()
            msgBox.setWindowTitle(_(u'Attention'))
            msgBox.setText('\n'.join(msg))
            msgBox.setIcon(QMessageBox.Information)
            msgBox.exec_() 
            return
        else:
            # ok on supprimer la table 
            x = self.view.countByTable[self.tableSchema['tableName']]
            
            
            self.view.tablesItem.remove(self)
            self.hide()
            self.view.tab.setDirty(True) 
            self.view.tab.executeQuery()
              
                
    def isInFilter(self, value):
        if value is None:
            return False
                         
        for index in range(1, len(value)):            
            c = value[index]                        
            if c[0] == 'ET' or c[0] == 'OU':
                isInFilter = self.isInFilter(c)
                if isInFilter:
                    return True                                                
            else:                
                (leftClause, operatorClause, rightClause, options) = c
                if leftClause.parentItem() == self:
                    return True 
                
                if isinstance(rightClause, ColumnItem):                
                    if rightClause.parentItem() == self:
                        return True 
                                
        return False
    
class MyQCheckBox(QCheckBox):
    def __init__(self, h,parent=None):
        QCheckBox.__init__(self, parent=parent)
        
            
        self.checkTrue = QPixmap(os.path.join(iconPrefix, 'check_true.png'))
        self.checkFalse = QPixmap(os.path.join(iconPrefix, 'check_false.png'))
        
        if h <= 17:
            self.checkTrue = self.checkTrue.scaledToHeight(h - 2)
            self.checkFalse = self.checkFalse.scaledToHeight(h - 2)
        self.h = h    
    #def paint(self, painter, option, widget):    
    def render(self,painter, point):    
        if self.checkState() :
            p = self.checkTrue
        else:
            p = self.checkFalse
        #print self.pos(),self.x(),self.y()
        y = self.y() + self.h/2 - p.height()/2
        painter.drawPixmap(self.x(), y, p)
        
    def newSize(self,h):
        self.h = h
        self.checkTrue = QPixmap(os.path.join(iconPrefix, 'check_true.png'))
        self.checkFalse = QPixmap(os.path.join(iconPrefix, 'check_false.png'))
        
        if h <= 17:
            self.checkTrue = self.checkTrue.scaledToHeight(h - 2)
            self.checkFalse = self.checkFalse.scaledToHeight(h - 2)
            
            
class ColumnItem(QGraphicsItem):
    def __init__(self, column2, fontsize, parent=None):
        
        from copy import deepcopy
        column = deepcopy(column2)
                          
        QGraphicsItem.__init__(self, parent)     
        self.isInSelect = False      
        self.preventCheckStateChanged = False           
        self.column = column                        
        self.setAcceptHoverEvents(True)      
        self.hoverState = False  
        
              
        font = QFont()
        
        font.setBold(False)        
        
        self.font = font
        
        
        self.linkState = False
        self.inEdge = []
        
        self.text = "%s (%d/%d)" % (column['name'], column['distinctCount'], column['count'])
        for (fk_table, fk_column) in column['fks']:
            self.text = self.text + "-> %s.%s" % (fk_table, fk_column)
            
        (w, h) = self.computeTextWidth (fontsize)
        
        self.rect = QRectF(0, 0, w, h)
        if self.parentItem().tableSchema['count'] > 0:
            self.lengthCount = (self.column['count'] * 1.0) / (1.0 * self.parentItem().tableSchema['count'])                
            self.lengthDistinctCount = (self.column['distinctCount'] * 1.0) / (1.0 * self.parentItem().tableSchema['count'])
        else:
            self.lengthCount = 0                
            self.lengthDistinctCount = 0
    
        self.setIconType()         
        self.check = MyQCheckBox(h)
        self.check.stateChanged.connect(self.checkClicked)
        
    def setIconType(self):
        column = self.column
        if column['type'] == 'STR':
            self.typeicon = QPixmap(os.path.join(iconPrefix, 'type_text.png'))
        elif column['type'] == 'INT' or column['type'] == 'DEC':
            self.typeicon = QPixmap(os.path.join(iconPrefix, 'type_num.png'))
        elif column['type'] == 'BOOL' :
            self.typeicon = QPixmap(os.path.join(iconPrefix, 'type_boolean.png'))
        elif column['type'] == 'TIME' :
            self.typeicon = QPixmap(os.path.join(iconPrefix, 'type_time.png'))
        elif column['type'] == 'DATETIME' or column['type'] == 'DATE':
            self.typeicon = QPixmap(os.path.join(iconPrefix, 'type_date.png'))   
        else:
            self.typeicon = QPixmap(os.path.join(iconPrefix, 'type_unkown.png'))
        
        h = self.rect.height()
        
        if h <= 17:
            self.typeicon = self.typeicon.scaledToHeight(h - 2)
        
    def checkClicked(self):     
        if not self.preventCheckStateChanged:            
            self.isInSelect = not self.isInSelect
            self.parentItem().view.tab.changeColumnSelected(self.parentItem(), self)
            self.update()
            
            
    def showDetail(self, location):        
        view = self.parentItem().view 
        dsId = view.datasourceId
        tableName = self.parentItem().name
        
        columnDetail = view.service.getColumnDetails(dsId, tableName, self.column['name'], self.column['typenatif'], self.column['type'])
        
        if hasattr(self, 'dialog') and  self.dialog is not None:
            del self.dialog
                        
        if self.column['type'] == 'INT' or self.column['type'] == 'DEC':
            self.dialog = ColumDetailDialogNumeric(columnDetail, self.isInSelect, view)
        elif self.column['type'] == 'DATE' or self.column['type'] == 'DATETIME':
            self.dialog = ColumDetailDialogDate(columnDetail, self.isInSelect, view)    
        else :
            self.dialog = ColumDetailDialog(columnDetail, self.isInSelect, view)
                        
        self.dialog.move(location)        
        self.dialog.show()
        self.dialog.raise_()
        self.dialog.activateWindow()
        
        self.dialog.exec_()
        
        
            
    def addInEdge(self, edge):        
        self.inEdge.append(edge)        
            
    def getLinkPoint(self):         
        return QPointF(self.parentItem().bounding.width() / 2.0, self.parentItem().bounding.height() / 2.0)
        
    def linkEnterEvent(self, TempLinkItem):
        self.linkState = True  # on utilise pur l'instant le hover mais on pourrait utiliser autre chose
        self.update()        
        
    def linkLeaveEvent(self, TempLinkItem):
        self.linkState = False  #
        self.update()    
            
    def setWidth(self, w):
        self.rect.setWidth(w)
            
    def computeTextWidth(self, fontsize):
        f = QFont()
        f.setPixelSize(fontsize)        
        fm = QFontMetrics(f)
        textWidthInPixels = fm.width(self.text)
        textHeightInPixels = fm.height()          
        return textWidthInPixels + 20, textHeightInPixels + 2
        
    def textSizeHasChanged(self, newfontsize):
        (w, h) = self.computeTextWidth (newfontsize)        
        self.rect = QRectF(0, 0, w, h)  # faire varier h pour changer la hauteur
        self.setIconType() 
        self.check.newSize(h)   
            
    def boundingRect(self):        
        return self.rect.adjusted(0, 0, 20, 0)  # 20 pour le bouton close en plus

    def hoverEnterEvent(self, event):                   
        self.hoverState = True    
        if self.parentItem():         
            self.parentItem().update()
        return QGraphicsItem.hoverEnterEvent(self, event)        
    
    def hoverLeaveEvent(self, event):        
        self.hoverState = False  
        if self.parentItem():      
            self.parentItem().update()     
        return QGraphicsItem.hoverLeaveEvent(self, event)
    
    def contextMenuEvent(self, event):
        pass
        
    def mousePressEvent(self, event):        
        if event.pos().x() < 20:
            self.check.setChecked(not self.check.checkState())
            self.update()
            
    def mouseReleaseEvent(self, event):        
        if event.pos().x() > 20 and event.pos().x() < self.boundingRect().width():             
            self.showDetail(event.screenPos())
    
            
    def paint(self, painter, option, widget): 
        h = self.boundingRect().height()               
        painter.fillRect(self.boundingRect(), Qt.lightGray)
        
        if self.hoverState:                        
            painter.fillRect(self.boundingRect(), QColor('red'))
        
        if self.linkState:                        
            painter.fillRect(self.boundingRect(), QColor('green'))    
                
        painter.setFont(self.font)
        painter.setPen(QPen(Qt.black))
        painter.drawText(self.rect.adjusted(+36, 0, 0, 0), Qt.AlignLeft, unicode(self.text))
        
        
        yicon = h / 2 - self.typeicon.height() / 2
        painter.drawPixmap(20, yicon, self.typeicon)
            
        painter.setPen(QPen(QColor('black'), 0.1, Qt.SolidLine))
        painter.drawRect(self.rect)
        
        painter.setPen(Qt.NoPen)
        painter.fillRect(QRectF(self.rect.width(), 0.0, 20.0 * self.lengthCount, 5.0), QColor('green'))
        painter.fillRect(QRectF(self.rect.width(), 5.0, 20.0 * self.lengthDistinctCount, 5.0), QColor('darkGreen'))
        
        ycheck = h / 2 - self.check.height() / 2
        self.check.render(painter, QPoint(0, ycheck))
        
        
class ColumDetailDialog(QDialog):
    def __init__(self, columnDetail, currentValue, parent=None):        
        QDialog.__init__(self, parent)
        self.detail = columnDetail
        layout = QGridLayout()
        self.setWindowTitle(_(u"Column Detail"))
                
        list = QListWidget()        
        layout.addWidget(list, 1, 0)
        
        
        self.setLayout(layout)
        self.setModal(True)
        for (val, count) in self.detail['distinctvalues']: 
            if not val:
                val = _(u'<vide>')           
            list.addItem('%s (%d)' % (val, count))
        
        
        copyButton = QPushButton(_(u"copy to clipboard"))
        copyButton.clicked.connect(self.copyToClipboard)
        layout.addWidget(copyButton, 2, 0)
        
    def copyToClipboard(self):        
        clipboard = QApplication.clipboard()        
        t = []
        for (val, count) in self.detail['distinctvalues']: 
            if not val:
                val = _(u'<vide>')           
            t.append('%s\t%d' % (val, count))
        clipboard.setText('\n'.join(t), QClipboard.Clipboard)
        
class ColumDetailDialogNumeric(QDialog):
    def __init__(self, columnDetail, currentValue, parent=None):
        try:
            QDialog.__init__(self, parent)
            self.detail = columnDetail
            layout = QGridLayout()
            self.setWindowTitle(_(u"Column Detail"))
            
            minLabel = QLabel(_(u"min"))
            maxLabel = QLabel(_(u"max"))
            ecartLabel = QLabel(_(u"Ecart Type"))
            moyenneLabel = QLabel(_(u"Moyenne"))
            medianeLabel = QLabel(_(u"Mediane"))
            modeLabel = QLabel(_(u"Mode"))
            
            
            minValue = QLabel('%.4g' % (columnDetail['min'],))
            maxValue = QLabel('%.4g' % (columnDetail['max'],))
            ecartValue = QLabel('%.4g' % (columnDetail['ecart'],))
            moyenneValue = QLabel('%.4g' % (columnDetail['avg'],))
            medianeValue = QLabel('%.4g' % (columnDetail['mediane'],))
            modeValue = QLabel('%.4g' % (columnDetail['mode'],))
            
            list = QListWidget()
            for (val, count) in self.detail['distinctvalues']: 
                if val is None:
                    list.addItem(_(u'<vide> (%(value)d)') % {'value':count})
                else:           
                    list.addItem('%g (%d)' % (val, count))
            
            
            layout.addWidget(minLabel, 0, 0)
            layout.addWidget(minValue, 0, 1)
            
            layout.addWidget(maxLabel, 1, 0)
            layout.addWidget(maxValue, 1, 1)
            
            layout.addWidget(ecartLabel, 2, 0)
            layout.addWidget(ecartValue, 2, 1)
            
            layout.addWidget(moyenneLabel, 3, 0)
            layout.addWidget(moyenneValue, 3, 1)
            
            layout.addWidget(medianeLabel, 4, 0)
            layout.addWidget(medianeValue, 4, 1)
            
            layout.addWidget(modeLabel, 5, 0)
            layout.addWidget(modeValue, 5, 1)
            
            layout.addWidget(list, 6, 0, 1, 2)
            
            
            copyButton = QPushButton(_(u"copy to clipboard"))
            copyButton.clicked.connect(self.copyToClipboard)
            layout.addWidget(copyButton, 7, 0, 1, 2)
            
            self.setLayout(layout)
            self.setModal(True)
        except Exception as e:
            print e
            print columnDetail
    
    def copyToClipboard(self):        
        clipboard = QApplication.clipboard()        
        t = []
        t.append(u'%s\t%.4f' % (_(u'min'), self.detail['min']))
        t.append(u'%s\t%.4f' % (_(u'max'), self.detail['max']))
        t.append(u'%s\t%.4f' % (_(u'ecart type'), self.detail['ecart']))
        t.append(u'%s\t%.4f' % (_(u'moyenne'), self.detail['avg']))
        t.append(u'%s\t%.4f' % (_(u'mediane'), self.detail['mediane']))
        t.append(u'%s\t%.4f' % (_(u'mode'), self.detail['mode']))
                
            
        for (val, count) in self.detail['distinctvalues']: 
            if not val:
                val = _(u'<vide>')           
            t.append('%s\t%d' % (val, count))
        clipboard.setText('\n'.join(t), QClipboard.Clipboard)
        
class ColumDetailDialogDate(QDialog):
    def __init__(self, columnDetail, currentValue, parent=None):
        try:
            QDialog.__init__(self, parent)
            self.detail = columnDetail
            layout = QGridLayout()
            self.setWindowTitle(_(u"Column Detail"))
            
            minLabel = QLabel(_(u"min"))
            maxLabel = QLabel(_(u"max"))
            moyenneLabel = QLabel(_(u"Moyenne"))
            medianeLabel = QLabel(_(u"Mediane"))            
            modeLabel = QLabel(_(u"Mode"))
            
            
            
            minValue = QLabel('%s' % (columnDetail['min'],))
            maxValue = QLabel('%s' % (columnDetail['max'],))  
            moyenneValue = QLabel('%s' % (columnDetail['avg'],))
            medianeValue = QLabel('%s' % (columnDetail['mediane'],))          
            modeValue = QLabel('%s' % (columnDetail['mode'],))
            
            list = QListWidget()
            for (val, count) in self.detail['distinctvalues']: 
                if not val:
                    val = _(u'<vide>')           
                list.addItem('%s (%d)' % (val, count))
            
            
            layout.addWidget(minLabel, 0, 0)
            layout.addWidget(minValue, 0, 1)
            
            layout.addWidget(maxLabel, 1, 0)
            layout.addWidget(maxValue, 1, 1)
            
            layout.addWidget(moyenneLabel, 2, 0)
            layout.addWidget(moyenneValue, 2, 1)
            
            layout.addWidget(medianeLabel, 3, 0)
            layout.addWidget(medianeValue, 3, 1)
            
            layout.addWidget(modeLabel, 4, 0)
            layout.addWidget(modeValue, 4, 1)
            
            layout.addWidget(list, 5, 0, 1, 2)
            
            
            copyButton = QPushButton(_(u"copy to clipboard"))
            copyButton.clicked.connect(self.copyToClipboard)
            layout.addWidget(copyButton, 6, 0, 1, 2)
            
            
                    
            
            self.setLayout(layout)
            self.setModal(True)
        except Exception as e:
            import traceback
            import sys
            traceback.print_exc(file=sys.stdout)             
            
            
    def copyToClipboard(self):        
        clipboard = QApplication.clipboard()        
        t = []
        t.append(u'%s\t%s' % (_(u'min'), self.detail['min']))
        t.append(u'%s\t%s' % (_(u'max'), self.detail['max']))   
        t.append(u'%s\t%s' % (_(u'moyenne'), self.detail['avg']))
        t.append(u'%s\t%s' % (_(u'mediane'), self.detail['mediane']))
        t.append(u'%s\t%s' % (_(u'mode'), self.detail['mode']))
                
            
        for (val, count) in self.detail['distinctvalues']: 
            if not val:
                val = _(u'<vide>')           
            t.append('%s\t%d' % (val, count))
        clipboard.setText('\n'.join(t), QClipboard.Clipboard)
        

