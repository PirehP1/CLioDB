# -*- coding: utf-8 -*-
"""
.. module:: transtypage
   :synopsis: Module de gestion du transtypage  
.. codeauthor:: pireh, amérique du nord, laurent frobert
"""
from PySide import QtCore, QtGui

class ComboDelegate(QtGui.QItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QtGui.QComboBox(parent)
        
        
        self.model = ['INT','DEC','STR','BOOL','DATE','TIME','DATETIME']
        editor.addItems(self.model)

        return editor

    def setEditorData(self, spinBox, index):
        value = index.model().data(index, QtCore.Qt.EditRole)
        try:
            i = self.model.index(value)
            spinBox.setCurrentIndex(i)
        except:
            pass

    def setModelData(self, spinBox, model, index):        
        value = self.model[spinBox.currentIndex()]

        model.setData(index, value, QtCore.Qt.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)
        
class changeTypeTable(QtGui.QDialog):
    def __init__(self,columns):        
        QtGui.QDialog.__init__(self)
        self.layout = QtGui.QGridLayout()
        self.setLayout(self.layout)
        
        self.view = QtGui.QTableView()
        self.model = CustomModel(columns)          
        self.view.setModel(self.model)
        
        self.layout.addWidget(self.view,0,0,1,2)
        
        cancelButton = QtGui.QPushButton(_(u'Annuler'))
        cancelButton.clicked.connect(self.cancelButtonClicked)
        
        validButton = QtGui.QPushButton(_(u'Valider'))
        validButton.clicked.connect(self.validButtonClicked)
        
        self.layout.addWidget(cancelButton,1,0)                
        self.layout.addWidget(validButton,1,1)
        
        self.resize(500,600)
        self.setModal(True)
        self.view.resizeColumnsToContents()
        
        self.delegate = ComboDelegate()
         
        self.view.setItemDelegateForColumn(2,self.delegate)
        
    def validButtonClicked(self):
        self.accept() 
        
    def cancelButtonClicked(self):
        self.reject()    
    
    def result(self):
        return self.model.getColumns()
        
    
        
class CustomModel(QtCore.QAbstractTableModel):
    def __init__(self,columns):
        QtCore.QAbstractTableModel.__init__(self)
        self.columns = columns
        self.header = [_(u'Nom colonne'),_(u'type natif'),_(u'nouveau type')]
        
    def getColumns(self):
        return self.columns    
    
    def rowCount(self, parent=QtCore.QModelIndex()):        
        return len(self.columns)    
    
    def columnCount(self, parent=QtCore.QModelIndex()):        
        return 3
    
    
    def headerData(self,section, orientation, role=QtCore.Qt.DisplayRole):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.header[section]
        else :
            return QtCore.QAbstractTableModel.headerData(self,section, orientation, role)
    
    def setData(self,index, value, role=QtCore.Qt.EditRole):
        row = index.row()
        column = index.column()
        
        if column == 2:
            self.columns[row][2] = value
        
    
    def flags(self,index):
        if index.column() == 2:
            return QtCore.Qt.ItemIsEnabled |  QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsSelectable        
        else:
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
    
    def data(self,index, role=QtCore.Qt.DisplayRole):
        row = index.row()
        column = index.column()
        if role == QtCore.Qt.DisplayRole:            
            return self.columns[row][column]            
            
        if role == QtCore.Qt.EditRole and column == 2:
            return self.columns[row][column]
   