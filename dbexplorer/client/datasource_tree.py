# -*- coding: utf-8 -*-
"""
.. module:: datasource_tree
   :synopsis: module de gestion de l'affichage de la liste des sources de données,des tables et des explorations
.. codeauthor:: pireh, amérique du nord, laurent frobert
"""
from PySide.QtCore import *
from PySide.QtGui import *



class CategoryItem(object):
    def __init__(self, name,parent=None):
        self.parentItem = parent  
        self.name = name      
        self.childItems = []        

    def appendChild(self, item):
        self.childItems.append(item)
        
    def removeChild(self, item):
        self.childItems.remove(item)    
    
        
    def child(self, row):
        return self.childItems[row]

    def childCount(self):
        return len(self.childItems)

    def columnCount(self):        
        return 1

    def data(self, column):
        if column == 0:            
            return self.name   
                     
        return None

    def parent(self):
        return self.parentItem

    def row(self):
        if self.parentItem:
            return self.parentItem.childItems.index(self)

        return 0
    
class TablesCategoryItem(CategoryItem):
    def __init__(self, parent=None):
        CategoryItem.__init__(self,_(u'Tables'),parent)

class ExplorationsCategoryItem(CategoryItem):
    def __init__(self, parent=None):
        CategoryItem.__init__(self,_(u'Explorations'),parent)
                
class DatasourceItem(object):
    def __init__(self, dsid,name, service,parent=None):
        self.parentItem = parent
        self.id = dsid
        self.name = name
        self.childItems = []
        self.service = service
    
    
    def removeDatasource(self):        
        response = self.service.removeDatasource(self.id)        
        return response
            
        
    def openDataSource(self):            
        self.childItems.append(TablesCategoryItem(self))
        self.childItems.append(ExplorationsCategoryItem(self))
        
        (error,tables) = self.service.getTablesNameById(self.id)
        if not error:
            for t in tables:                    
                tableItem = TableItem(t,self.childItems[0])
                self.childItems[0].appendChild(tableItem)      
        else:
            print error
                  
        (error,explos) = self.service.getExplorationsNameByDsId(self.id)
        if not error:
            if len(explos)>0:
                for (idExplo,nameExplo) in explos:
                    exploItem = ExplorationItem(idExplo,nameExplo,self.childItems[1])
                    self.childItems[1].appendChild(exploItem)
                        

    def appendChild(self, item):
        self.childItems.append(item)

    def child(self, row):
        return self.childItems[row]

    def childCount(self):
        return len(self.childItems)

    def columnCount(self):
        #return len(self.itemData)
        return 1

    def data(self, column):
        if column == 0:            
            return self.name   
                     
        return None

    def parent(self):
        return self.parentItem

    def row(self):
        if self.parentItem:
            return self.parentItem.childItems.index(self)

        return 0
    
class TableItem(object):
    def __init__(self, name, parent=None):
        self.parentItem = parent        
        self.name = name        
    
    def childCount(self):
        return 0

    def columnCount(self):
        #return len(self.itemData)
        return 1

    def data(self, column):
        if column == 0:            
            return self.name   
                     
        return None

    def parent(self):
        return self.parentItem

    def row(self):
        if self.parentItem:
            return self.parentItem.childItems.index(self)

        return 0

class ExplorationItem(object):
    def __init__(self, id,name, parent=None,explorationTab=None):
        self.explorationTab = explorationTab # renseigne quand l'explo est ouverte
        self.parentItem = parent    
        self.id = id    
        self.name = name        
    
    
    
    def childCount(self):
        return 0

    def columnCount(self):        
        return 1

    def data(self, column):
        if column == 0:            
            return self.name   
                     
        return None

    def parent(self):
        return self.parentItem

    def row(self):
        if self.parentItem:
            return self.parentItem.childItems.index(self)

        return 0
   
class TreeModel(QAbstractItemModel):
    def __init__(self, service, parent=None):
        super(TreeModel, self).__init__(parent)
        self.service = service                
        self.load()
    
    
            
    def load(self):
        datasources = self.service.getDatasourcesNameList()
        
        self.rootItem = CategoryItem(_(u'datasources'),None)
        self.setupModelData(datasources, self.rootItem)
        
        
    def columnCount(self, parent):
        if parent.isValid():
            return parent.internalPointer().columnCount()
        else:
            return self.rootItem.columnCount()

    def data(self, index, role):
        if not index.isValid():
            return None

        if role != Qt.DisplayRole:
            return None

        item = index.internalPointer()

        return item.data(index.column())

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags

        return Qt.ItemIsEnabled #| Qt.ItemIsSelectable

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.rootItem.data(section)

        return None

    def index(self, row, column, parent):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        childItem = parentItem.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()

        childItem = index.internalPointer()
        parentItem = childItem.parent()

        if parentItem == self.rootItem:
            return QModelIndex()

        return self.createIndex(parentItem.row(), 0, parentItem)

    def rowCount(self, parent):
        if parent.column() > 0:
            return 0

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        return parentItem.childCount()

    def setupModelData(self, datasources, parent):
        
        if not datasources:
            return 
        
        for (dsId,dsName) in datasources:
            dsItem = DatasourceItem(dsId,dsName, self.service,parent)
            parent.appendChild(dsItem)
    
    def removeExploration(self,explorationItem):
        parent = explorationItem.parentItem
        parent.removeChild(explorationItem)
        self.reset()
        
        
                             
    def newExploration(self,did,explorationTab):
        for it in self.rootItem.childItems:
            if it.id == did:
                dsItem = it
                
        if not dsItem:
            #id de la datasource not found
            pass
        else:  
            exploItem = ExplorationItem(-1,explorationTab.exploName,dsItem.childItems[1],explorationTab = explorationTab)
            dsItem.childItems[1].appendChild(exploItem)
            self.rowsInserted.emit(dsItem.childItems[1], dsItem.childItems[1].childCount()-1, dsItem.childItems[1].childCount()-1)
    
    def newTable(self,dsItem,tablename):            
        if not dsItem:
            #id de la datasource not found
            pass
        else:  
            tableItem = TableItem(tablename,dsItem.childItems[0])
            dsItem.childItems[0].appendChild(tableItem)
            self.rowsInserted.emit(dsItem.childItems[0], dsItem.childItems[0].childCount()-1, dsItem.childItems[0].childCount()-1)
            
    def getDatasourceItemById(self,did):
        for it in self.rootItem.childItems:            
            if it.id == did:
                return it
            
        return None
    
    def getDatasourceItemByName(self,dsname):
        for it in self.rootItem.childItems:            
            if it.name == dsname:
                return it
            
        return None
    
    def getIndexOfDatasourceItem(self,item):                
        return self.createIndex( self.rootItem.childItems.index(item), 0, QModelIndex())
        
                
    def getExplorationItemForTab(self,did,explorationTab):
        for it in self.rootItem.childItems:
            if it.id == did:
                dsItem = it
        if not dsItem:
            #id de la datasource not found
            pass
        else:          
            for explo in dsItem.childItems[1].childItems:
                if explo.explorationTab == explorationTab:
                    return explo
                
            
    def getExplorationItemForIds(self,did,explorationId):
        dsItem = None
        for it in self.rootItem.childItems:
            if it.id == did:
                dsItem = it
                
        if not dsItem:
            #id de la datasource not found
            pass
        else:          
            for explo in dsItem.childItems[1].childItems:
                if explo.id == explorationId:
                    return explo
                    
                
    def newDatasource(self,datasourceId,datasourceName):
        dsItem = DatasourceItem(datasourceId,datasourceName, self.service,self.rootItem)
        self.rootItem.appendChild(dsItem)
        
        self.rowsInserted.emit(self.rootItem, self.rootItem.childCount()-1, self.rootItem.childCount()-1)
    
    def closeDatasource(self,dsid):
        for it in self.rootItem.childItems:
            if it.id == dsid:
                dsItem = it
                
        if not dsItem:
            #id de la datasource not found
            pass
        else:              
            dsItem.childItems = []
            self.rowsRemoved.emit(dsItem, 0, 0)
            
    def removeDatasource(self,dsid):
        for it in self.rootItem.childItems:
            if it.id == dsid:
                dsItem = it
                
        if not dsItem:
            #id de la datasource not found
            pass
        else:              
            self.rootItem.childItems.remove(dsItem)
            dsItem.childItems = []        
            self.reset()    
            
    
class DatasourceTreeView(QTreeView):
    def __init__(self,service,mainWindow,parent = None):
        QTreeView.__init__(self,parent)
        self.service = service
        self.mainWindow = mainWindow
        self.setExpandsOnDoubleClick(False)
        
        self.doubleClicked[QModelIndex].connect(self.doubleclick)
        
        self.pressed.connect(self.pressedOnItem)
           
        self.setDragDropMode(QAbstractItemView.DragOnly)
        self.setDragEnabled(True)        
        self.setIndentation(15)
    
    def newExploration(self,did,explorationTab):
        self.model().newExploration(did,explorationTab)
    
    def getExplorationItemForTab(self,did,explorationTab):
        return self.model().getExplorationItemForTab(did,explorationTab)
            
    def newDatasource(self,datasourceId,datasourceName):
        self.model().newDatasource(datasourceId, datasourceName)
        
    def doubleclick(self,index):
        item = index.internalPointer()
        if isinstance(item,DatasourceItem):
            
            if self.mainWindow.currentDatasource and self.mainWindow.currentDatasource[0] == item.id:
                self.expand(index)
                return #this datasource is already open 
                            
            if self.mainWindow.canOpenDatasource():
                                                                             
                item.openDataSource()
                self.mainWindow.stopWait()
                self.collapseAll()                
                self.mainWindow.setCurrentDatasource(item.id,item.name)                
                self.expand(index)
        elif isinstance(item,ExplorationsCategoryItem) or isinstance(item,TablesCategoryItem):
            if not self.isExpanded(index):
                self.expand(index)
            else:
                self.collapse(index)
        elif isinstance(item,ExplorationItem):
            if item.explorationTab:
                return #exploration already open
            else:
                self.mainWindow.openExploration(item)
    
            
    def pressedOnItem(self,index):
        item = index.internalPointer()        
        if isinstance(item,TableItem) and QApplication.mouseButtons() != Qt.RightButton:
            mimeData = QMimeData()
            mimeData.setData('application/x-dnditemdata', str(item.name))            
            lab = QLabel(item.name)
            pixmap = QPixmap(lab.sizeHint())
            lab.render(pixmap)
            drag = QDrag(lab)
            drag.setMimeData(mimeData)            
            drag.setPixmap(pixmap)                                    
            dropAction = drag.start(Qt.MoveAction)      
        
        
    def closeDatasource(self,dsid):
        self.model().closeDatasource(dsid)
    
        
    def contextMenuEvent(self,  event):              
        index = self.indexAt(event.pos())
        item = index.internalPointer()        
        
        if isinstance(item,TableItem):
            return # for now
            menu = QMenu()
            changeTypeAction = menu.addAction(_(u"Changement de type"))            
            selectedAction = menu.exec_(event.globalPos())
            
            if selectedAction == changeTypeAction:                   
                self.mainWindow.changeTypeTable(item.name)                
                
        elif isinstance(item,ExplorationsCategoryItem) :
            menu = QMenu()
            newExplorationAction = menu.addAction(_(u"Nouvelle exploration"))            
            selectedAction = menu.exec_(event.globalPos())
            
            if selectedAction == newExplorationAction:                    
                self.mainWindow.newExploration()
                self.expand(index)
                
        elif isinstance(item,DatasourceItem):
            if self.mainWindow.currentDatasource and self.mainWindow.currentDatasource[0] == item.id:                
                menu = QMenu()            
                clauseDatasourceAction = menu.addAction(_(u"fermer la base de données"))
                importExplorationAction = menu.addAction(_(u"Importer une exploration"))
                
                #importFichierCsvAction = menu.addAction(_(u"Importer un fichier CSV"))
                            
                selectedAction = menu.exec_(event.globalPos())
                if selectedAction == clauseDatasourceAction:
                    self.mainWindow.closeCurrentDatasource()                                        
                    self.collapseAll()
                elif selectedAction == importExplorationAction:
                    self.mainWindow.importExploration(item.id)
                    
                    
                    
            else:    
                menu = QMenu()            
                openDatasourceAction = menu.addAction(_(u"Ouvrir la base de données")) 
                transtypageAction = menu.addAction(_(u"Transtypage"))
                removeDatasourceAction = menu.addAction(_(u"Supprimer la base de données"))  

                selectedAction = menu.exec_(event.globalPos())
                if selectedAction == openDatasourceAction:
                    #close
                    if self.mainWindow.canOpenDatasource():                                                             
                        item.openDataSource()
                        self.mainWindow.stopWait()
                        self.collapseAll()
                        #check if we have to save something
                        self.expand(index)
                        
                        self.mainWindow.setCurrentDatasource(item.id,item.name)
                elif selectedAction == removeDatasourceAction:
                    reply = QMessageBox.question(self, item.name,_(u"Voulez vous vraiment supprimer cette source de données ?"),
                                                  QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            
                    if reply == QMessageBox.Yes:
                        response = item.removeDatasource()
                        if response == 'ok':
                            self.model().removeDatasource(item.id)                                                                
                            pass
                elif selectedAction == transtypageAction:                    
                    self.mainWindow.transtypageDatasource(item.id)     
                                
        elif isinstance(item,ExplorationItem) :
            menu = QMenu()
            openExplorationAction = menu.addAction(_(u"Ouvrir l'exploration"))
            exporterExplorationAction = menu.addAction(_(u"Exporter l'exploration"))
            saveExplorationAction = menu.addAction(_(u"Sauver l'exploration"))
            closeExplorationAction = menu.addAction(_(u"Fermer l'exploration"))
            copyExplorationAction = menu.addAction(_(u"Copier l'exploration"))            
            changeNameExplorationAction = menu.addAction(_(u"Modifier le nom de l'exploration"))
            removeExplorationAction = menu.addAction(_(u"Supprimer l'exploration"))
            
            if item.explorationTab: # tab deja ouvert
                openExplorationAction.setEnabled(False)
                exporterExplorationAction.setEnabled(False)
                removeExplorationAction.setEnabled(False)
                if not item.explorationTab.dirty:
                    saveExplorationAction.setEnabled(False)
            else: # exploration pas encore ouverte
                saveExplorationAction.setEnabled(False)
                closeExplorationAction.setEnabled(False)
                copyExplorationAction.setEnabled(False)
                changeNameExplorationAction.setEnabled(False)
                
            selectedAction = menu.exec_(event.globalPos())
            
            if selectedAction == copyExplorationAction:                    
                self.mainWindow.copyExploration(item.explorationTab)                
            elif selectedAction == saveExplorationAction:                    
                self.mainWindow.saveExploration(item.explorationTab)
            elif selectedAction == exporterExplorationAction:
                self.mainWindow.exportExploration(item)    
            elif selectedAction == openExplorationAction:                    
                self.mainWindow.openExploration(item)
            elif selectedAction == closeExplorationAction:                    
                self.mainWindow.closeExploration(item)    
            elif selectedAction == changeNameExplorationAction:
                self.mainWindow.changeNameExploration(item)
            elif selectedAction == removeExplorationAction:  
                reply = QMessageBox.question(self, item.name,_(u"Voulez vous vraiment supprimer cette exploration ?"),
                                                  QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            
                if reply == QMessageBox.Yes:
                    response = self.service.removeExploration(item.id)
                    if response == 'ok':
                        self.model().removeExploration(item)                        
                        pass
        
