# -*- coding: utf-8 -*-
"""
.. module:: edit_join_dialog
   :synopsis: Module pour l'affichage d'une boîte de dialogue pour la gestion des 'join'
.. codeauthor:: pireh, amérique du nord, laurent frobert
"""
from PySide.QtCore import *
from PySide.QtGui import *

def getTableName(tableItem):
        if tableItem.alias:
            return tableItem.alias
        else:
            return tableItem.name
        
class JoinGroupModel(QAbstractTableModel):
    def __init__(self,joinList):
        QAbstractTableModel.__init__(self)
        self.joinList = joinList
        
    def rowCount(self,parent=QModelIndex()):
        if parent.isValid():
            return 0
        else:
            return len(self.joinList)
    
    def columnCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        else:
            return 3
    
    
        
    def data(self,index, role=Qt.DisplayRole):        
        (joinType,tableItem,col1,col2) = self.joinList[index.row()]         
        if role == Qt.DisplayRole:             
            if index.row() == 0: #first line
                if index.column() == 1:
                    return getTableName(tableItem)
                else:
                    return ""
            else: #other line                
                if index.column() == 0:
                    return joinType 
                elif index.column() == 1:
                    return getTableName(tableItem)
                elif index.column() == 2:
                    if col1 and col2:
                        ti1 = col1.parentItem()                                        
                        ti2 = col2.parentItem()                                                            
                        return "on %s.%s=%s.%s"%(getTableName(ti1),col1.column['name'],getTableName(ti2),col2.column['name'])
                    else:
                        return "A définir !"
                     
        elif role == Qt.EditRole:                        
            if index.row() == 0: #first line
                return None # no edit of the firstline
                    
            else:                
                if index.column() == 0:
                    return joinType 
                elif index.column() == 1:
                    return tableItem
                elif index.column() == 2:                    
                    return (col1,col2)     
        
        return None
    
        
    
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        horizontalHeader=[_(u'type'),_(u'table'),_(u'champs de jointure')]
        
                
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal :
                return horizontalHeader[section]
            
            elif section>0 : # vertical header
                return section        
        
        return None
    
    def setData(self,index, value, role=Qt.EditRole):
        if index.column() == 2 and index.row() != 0:
            (newcol1,newcol2) = value
            (joinType,tableItem,col1,col2) = self.joinList[index.row()]
            self.joinList[index.row()]  = (joinType,tableItem,newcol1,newcol2) 
        elif index.column() == 0 and index.row() != 0:
            (joinType,tableItem,col1,col2) = self.joinList[index.row()]
            self.joinList[index.row()]  = (value,tableItem,col1,col2)    
        else: # pour le moment interdiction de modifier autre chose que la colonne 2 (=les criteres du join)
            return False
        
        return True
    
    def flags(self,index):
        if index.column() == 1:
            return Qt.ItemIsEnabled | ~ Qt.ItemIsEditable | Qt.ItemIsSelectable
        elif index.row() == 0:
            return Qt.ItemIsEnabled | ~ Qt.ItemIsEditable | Qt.ItemIsSelectable
        else:
            return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable
    
    def moveUp(self,index):
        self.joinList.insert(index-1, self.joinList.pop(index))
        self.reset()
    
    def moveDown(self,index):
        self.joinList.insert(index+1, self.joinList.pop(index))
        self.reset()    
        
    def remove(self,index):
        self.joinList.pop(index)
        self.reset()
    
class JoinFieldEditor(QWidget): # editeur visuel pour selectionner les colonnes de jointure, affichge de 2 combo avec 
    def __init__(self,joinList,parent=None):
        QWidget.__init__(self,parent)
        layout = QGridLayout()
        layout.setContentsMargins(0,0,0,0)
        self.setLayout(layout)
        self.setAutoFillBackground(True)
        onlabel = QLabel("ON")
        self.leftCombo = QComboBox()
        equallabel = QLabel("=")
        self.rightCombo = QComboBox()
        
        layout.addWidget(onlabel,0,0)
        layout.addWidget(self.leftCombo,0,1)
        layout.addWidget(equallabel,0,2)
        layout.addWidget(self.rightCombo,0,3)
        
        #init model 
        self.model =  FieldsModel(joinList)
        self.leftCombo.setModel(self.model)
        self.rightCombo.setModel(self.model)
            
            
        
        
class FieldsModel(QAbstractListModel):
    def __init__(self,joinList):
        QAbstractListModel.__init__(self)
        self.fieldsList = []
        
        # construct the field list        
        for (__,tableItem,__,__) in joinList:
            for columnItem in tableItem.columnsItem:
                self.fieldsList.append(columnItem)
        
        
    def rowCount(self,parent= QModelIndex()):
        return len(self.fieldsList)
     
    def data(self, index, role = Qt.DisplayRole):        
        if role == Qt.DisplayRole:
            columnItem = self.fieldsList[index.row()]
            tableItem = columnItem.parentItem()
            t1 = getTableName(tableItem) 
            return  "%s.%s"%(t1,columnItem.column['name'])
        elif role == Qt.EditRole :            
            return self.fieldsList[index.row()]         
            
        
        
        
        return None       
        
class JoinDelegate(QStyledItemDelegate):
    def __init__(self, parent = None):
        QStyledItemDelegate.__init__(self, parent)
                
        
        
    def createEditor(self, parent, option, index):
        
        if not index.isValid() or index.row() == 0:
            return QStyledItemDelegate.createEditor(self,parent,option,index)
        
        editor = QComboBox(parent)
        model = ["join","outer join"]
        editor.setModel(QStringListModel(model)) #join=inner join
        for i in range(len(model)):
            editor.setItemData(i,model[i])        
        return editor

    def setEditorData(self, editor, index):
        if not index.isValid()  or index.row() == 0:
            return QStyledItemDelegate.setEditorData(self,editor,index)
        
        joinType = index.model().data(index, Qt.EditRole)        
        
        index = editor.findData(joinType,Qt.ItemDataRole)
        
        editor.setCurrentIndex(index)
            
    def setModelData(self, editor, model, index):
        if not index.isValid()  or index.row() == 0:
            return QStyledItemDelegate.setModelData(self,editor,model,index)
        
        index1 = editor.currentIndex()
        
        
        joinType = editor.itemData(index1,Qt.EditRole)        
        
        model.setData(index,joinType,Qt.EditRole)
        
        
    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)
            
class JoinFieldDelegate(QStyledItemDelegate):
    def __init__(self, joinList,parent = None):
        QStyledItemDelegate.__init__(self, parent)
        self.joinList = joinList        
        
        
    def createEditor(self, parent, option, index):
        
        if not index.isValid() or index.row() == 0:
            return QStyledItemDelegate.createEditor(self,parent,option,index)
        
        editor = JoinFieldEditor(self.joinList,parent)
        
                
        return editor

    def setEditorData(self, editor, index):
        if not index.isValid()  or index.row() == 0:
            return QStyledItemDelegate.setEditorData(self,editor,index)
        
        (col1,col2) = index.model().data(index, Qt.EditRole)        
        
        index = editor.leftCombo.findData(col1,Qt.EditRole)
        editor.leftCombo.setCurrentIndex(index)
        
        
        
        index2 = editor.rightCombo.findData(col2,Qt.EditRole)
        editor.rightCombo.setCurrentIndex(index2)
        
        
    def setModelData(self, editor, model, index):
        if not index.isValid()  or index.row() == 0:
            return QStyledItemDelegate.setModelData(self,editor,model,index)
        
        index1 = editor.leftCombo.currentIndex()
        index2 = editor.rightCombo.currentIndex()
        
        col1 = editor.leftCombo.itemData(index1,Qt.EditRole)
        col2 = editor.rightCombo.itemData(index2,Qt.EditRole)
        
        model.setData(index,(col1,col2),Qt.EditRole)
        
        
    def updateEditorGeometry(self, editor, option, index):
        if index.isValid() and index.column() != 2:
            return QStyledItemDelegate.updateEditorGeometry(self,editor,option,index)
                
        editor.setGeometry(option.rect)

            

class EditJoinGroupDialog(QDialog):
    def __init__(self,joinGroup):
        QDialog.__init__(self)
        self.joinList = []
        self.joinList.append((None,joinGroup.firstTableItem,None,None))
        for (joinType,tableItem,col1,col2,__) in joinGroup.links:
            self.joinList.append((joinType,tableItem,col1,col2))
            
        self.setModal(True)
        layout = QGridLayout()
        self.listW = QTableView(self)
        
        model = JoinGroupModel(self.joinList)
        
        self.listW.setAlternatingRowColors(True)        
        self.listW.verticalHeader().setClickable(True)
        
        delegate = JoinFieldDelegate(self.joinList,self.listW)
        self.listW.setItemDelegateForColumn(2,delegate)
        delegateJoin = JoinDelegate(self.listW)
        self.listW.setItemDelegateForColumn(0,delegateJoin)
        
        self.listW.setModel(model)
        for i in range(self.listW.model().columnCount()):
                self.listW.resizeColumnToContents(i)

           
        layout.addWidget(self.listW,0,0,1,7)
        
        self.upButton = QPushButton(_(u"monter"))
        self.downButton = QPushButton(_(u"descendre"))
        
        self.validButton = QPushButton(_(u"valider"))
        self.cancelButton = QPushButton(_(u"annuler"))
        
        self.removeButton = QPushButton(_(u"supprimer"))
        
        self.upButton.clicked.connect(self.moveUpRow)
        self.downButton.clicked.connect(self.moveDownRow)
        
        self.removeButton.clicked.connect(self.removeRow)
        
        self.validButton.clicked.connect(self.checkIfValid)
        self.cancelButton.clicked.connect(self.reject)
        
        layout.addWidget(self.cancelButton,1,0)
        layout.addWidget(self.removeButton,1,2)
        
        layout.addWidget(self.upButton,1,3)
        layout.addWidget(self.downButton,1,4)
        
        layout.addWidget(self.validButton,1,6)
        
        self.setLayout(layout)
        self.setWindowTitle(_(u"édition des jointures"))
        self.resize(600,200)
                
        
    def checkIfValid(self):
        # check if allJoinType are defined        
        
        #simulation d'un click pour etre sur que le delegate editor a bien valider la derniere modif
        self.listW.mousePressEvent(QMouseEvent(QEvent.MouseButtonPress,QPoint(0,0),Qt.MouseButton.LeftButton,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier))
        
        index=0
        allowedCol=[]
        joinTypeErrorExists = []
        joinFieldEmptyExists = set([])
        joinFieldNotInPrecExists = set([])
        joinFieldAtLeastItSelf = set([])
        
        for (joinType,tableItem,col1,col2) in self.joinList:            
            allowedCol = allowedCol+tableItem.columnsItem
            if index >0:
                if not joinType:
                    joinTypeErrorExists.append(index)
                   
                if not col1 or not col2:
                    joinFieldEmptyExists.add(index)
                
                if col1 and not col1 in allowedCol:
                    joinFieldNotInPrecExists.add(index)
                
                if col2 and not col2 in allowedCol:
                    joinFieldNotInPrecExists.add(index)    
                
                if col1.parentItem() != tableItem and col2.parentItem() != tableItem:
                    joinFieldAtLeastItSelf.add(index)   
                      
            index+=1    
        
        if not joinTypeErrorExists and not joinFieldEmptyExists and not joinFieldNotInPrecExists and not joinFieldAtLeastItSelf:
            self.accept()
        else:            
            msg=[]
            if joinTypeErrorExists:
                msg.append(_(u"il manque le type de jointure pour les jointures : %(msg)s")%{'msg':', '.join(map(str, joinTypeErrorExists))}) 
            if joinFieldEmptyExists:
                msg.append(_(u"il manque des colonnes de jointures pour les jointures : %(msg)s")%{'msg': ', '.join(map(str, joinFieldEmptyExists))}) 
            if joinFieldNotInPrecExists:
                msg.append(_(u"les colonnes de jointures sont invalides pour les jointures  : %(msg)s")%{'msg': ', '.join(map(str, joinFieldNotInPrecExists))}) 
            if joinFieldAtLeastItSelf:
                msg.append(_(u"une colonne de la table doit au moins apparaitre dans sa propre jointure   : %(msg)s")%{'msg': ', '.join(map(str, joinFieldAtLeastItSelf))})
                
            msgBox = QMessageBox()
            msgBox.setText('\n'.join(msg))
            msgBox.setIcon(QMessageBox.Warning)
            msgBox.exec_()        
            
    def result(self):
        return self.joinList
        
    def resizeMe(self):                
        self.resize(500,200)
    
    def removeRow(self):        
        index = self.listW.selectedIndexes()[0].row()                    
        self.listW.model().remove(index)
                
        pass
    
        
    def moveUpRow(self):
        if len(self.listW.selectedIndexes())>0:
            index = self.listW.selectedIndexes()[0].row()
            if index>0:        
                self.listW.model().moveUp(index)
    
    def moveDownRow(self):
        if len(self.listW.selectedIndexes())>0:
            index = self.listW.selectedIndexes()[0].row()
            if index<self.listW.model().rowCount()-1:        
                self.listW.model().moveDown(index)
            
    
        


