# -*- coding: utf-8 -*-
#
"""
.. module:: croisement
   :synopsis: module de génération de la fenêtre modale pour la sélection des croisements de données 
.. codeauthor:: pireh, amérique du nord, laurent frobert
"""
from PySide import QtCore, QtGui

class YesNoDelegate(QtGui.QStyledItemDelegate):
    def __init__(self, parent = None):
        QtGui.QStyledItemDelegate.__init__(self, parent)
    def createEditor(self, parent, option, index):
        
        if not index.isValid() :
            return QtGui.QStyledItemDelegate.createEditor(self,parent,option,index)
        
        editor = QtGui.QComboBox(parent)
        model = ["Oui","Non"]
        editor.setModel(QtGui.QStringListModel(model)) #join=inner join
        for i in range(len(model)):
            editor.setItemData(i,model[i])        
        return editor

    def setEditorData(self, editor, index):
        if not index.isValid()  :
            return QtGui.QStyledItemDelegate.setEditorData(self,editor,index)
        
        response = index.model().data(index, QtCore.Qt.EditRole)        
        
        index = editor.findData(response,QtCore.Qt.ItemDataRole)
        
        editor.setCurrentIndex(index)
            
    def setModelData(self, editor, model, index):
        if not index.isValid() :
            return QtGui.QStyledItemDelegate.setModelData(self,editor,model,index)
        
        index1 = editor.currentIndex()
        
        
        response = editor.itemData(index1,QtCore.Qt.EditRole)        
        
        model.setData(index,response,QtCore.Qt.EditRole)
        
        
    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

class QualificatifDelegate(QtGui.QStyledItemDelegate):
    def __init__(self, parent = None):
        QtGui.QStyledItemDelegate.__init__(self, parent)
        
    def createEditor(self, parent, option, index):
        
        if not index.isValid() :
            return QtGui.QStyledItemDelegate.createEditor(self,parent,option,index)
        
        editor = QtGui.QComboBox(parent)
        model = ["Qualitatif","Quantitatif"]
        editor.setModel(QtGui.QStringListModel(model)) #join=inner join
        for i in range(len(model)):
            editor.setItemData(i,model[i])        
        return editor

    def setEditorData(self, editor, index):
        if not index.isValid()  :
            return QtGui.QStyledItemDelegate.setEditorData(self,editor,index)
        
        response = index.model().data(index, QtCore.Qt.EditRole)        
        
        index = editor.findData(response,QtCore.Qt.ItemDataRole)
        
        editor.setCurrentIndex(index)
            
    def setModelData(self, editor, model, index):
        if not index.isValid() :
            return QtGui.QStyledItemDelegate.setModelData(self,editor,model,index)
        
        index1 = editor.currentIndex()
        
        
        response = editor.itemData(index1,QtCore.Qt.EditRole)        
        
        model.setData(index,response,QtCore.Qt.EditRole)
        
        
    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)


class SelectedColumnsModel(QtCore.QAbstractTableModel):
    def __init__(self,selectedColumns):
        
        QtCore.QAbstractTableModel.__init__(self)
        
        self.model = []
        for (tableItem,columnItem,other) in selectedColumns:
            #type = columnItem.column['typenatif']
            type = columnItem.column['type']
            if type=='STR':
                qualificatif = 'Qualitatif'
            else:
                qualificatif = 'Quantitatif'
            exclus = False    
            self.model.append([(tableItem,columnItem),type,qualificatif,exclus])
            
            
        #tri en fonction du type
        model2=[]
        
        for index in reversed(range(0,len(self.model))):
            if self.model[index][1] == 'INT':
                v = self.model.pop(index)
                model2.append(v)     
        
        for index in reversed(range(0,len(self.model))):
            if self.model[index][1] == 'DEC':
                v = self.model.pop(index)
                model2.append(v)     
        
        for index in reversed(range(0,len(self.model))):
            if self.model[index][1] == 'STR':
                v = self.model.pop(index)
                model2.append(v)
        for index in reversed(range(0,len(self.model))):            
            v = self.model.pop(index)
            model2.append(v)
                        
        
        self.model = model2 
           
    def rowCount(self, *args, **kwargs):
        return len(self.model)
    
    def columnCount(self,parent=QtCore.QModelIndex()):
        return 4
    
    def setData(self,index, value, role=QtCore.Qt.EditRole):
        row = index.row()
        col = index.column()
        
        if col == 2:
            self.model[row][col] = value
            
        elif col == 3:
            if value == 'Oui':
                self.model[row][col] = True
            else :
                self.model[row][col] = False    
    
    def data(self,index, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:            
            row = index.row()
            col = index.column()
            if col == 0:
                return self.model[row][0][1].column['name']
            elif col == 1:
                return self.model[row][1]
            elif col == 2:
                return self.model[row][2]
            elif col == 3:
                if self.model[row][3]:
                    return 'Oui'
                else:
                    return 'Non'
        
        if role == QtCore.Qt.EditRole:
            row = index.row()
            col = index.column()
            if col == 2:
                return self.model[row][2]
            elif col == 3:
                if self.model[row][3]:
                    return 'Oui'
                else :
                    return 'Non'
        
       
    def flags(self,index):
        if index.column() in [0,1]:
            return QtCore.Qt.ItemIsEnabled | ~ QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsSelectable
        else:
            return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
    
    
    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        horizontalHeader=[_(u'Nom du champs'),_(u'Type'),_(u'Qualificatif'),_(u'Exclus')]
        
                
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal :
                return horizontalHeader[section]
            
        return None
             
class QualificationModal(QtGui.QDialog):
    def __init__(self,tab):
        QtGui.QDialog.__init__(self)
        self.tab = tab
        
        self.setWindowTitle(_(u'Qualification des variables'))
        layout = QtGui.QGridLayout()
        self.setLayout(layout)
        self.resize(500,300)
        self.tabview = QtGui.QTableView()
        exclusionDelegate = YesNoDelegate(self.tabview)
        self.tabview.setItemDelegateForColumn(3,exclusionDelegate)
        
        qualificatifDelegate = QualificatifDelegate(self.tabview)
        self.tabview.setItemDelegateForColumn(2,qualificatifDelegate)
        
        self.tabmodel = SelectedColumnsModel(tab.selectedColumns)
        self.tabview.setModel(self.tabmodel)
        layout.addWidget(self.tabview)
        
        valid = QtGui.QPushButton(_(u'Validez'))
        valid.clicked.connect(self.accept)
        
        cancel = QtGui.QPushButton(_(u'Annulez'))
        cancel.clicked.connect(self.reject)
        
        layout.addWidget(valid)
        layout.addWidget(cancel)
        
        
        self.tabview.resizeColumnsToContents()                    
        self.tabview.resizeRowsToContents()
        
    def result(self):
        return self.tabmodel.model
    
    
        