# -*- coding: utf-8 -*-
"""
.. module:: customsql
   :synopsis: module d'affichage de la fenêtre permettant d'executer des requêtes spécifiques
.. codeauthor:: pireh, amérique du nord, laurent frobert
"""
from PySide import QtGui,QtCore
class CustomSQL(QtGui.QDialog):
    def __init__(self,service,datasourceId,sql,view,parent=None):
        QtGui.QDialog.__init__(self,parent=parent)
        self.view = view
        self.service = service
        self.datasourceId = datasourceId
        
        self.editableZone  = QtGui.QPlainTextEdit()
        
        
        self.executeButton = QtGui.QPushButton(_(u"Execute"))
        self.executeButton.clicked.connect(self.executeQuery)        
        
        self.exportButton = QtGui.QPushButton(_(u"Export"))
        self.exportButton.clicked.connect(self.exportQuery)
        
        self.resultCount = QtGui.QLabel("") 
        
        self.lineAction = QtGui.QFrame()
        lineActionLayout = QtGui.QGridLayout()
        lineActionLayout.setContentsMargins(0,0,0,0)
        xpos = 0     
        lineActionLayout.addWidget(self.executeButton,0,xpos)
        xpos+=1
        self.spacer = QtGui.QSpacerItem(1,1) 
        lineActionLayout.addItem(self.spacer,0,xpos)       
        xpos+=1
        lineActionLayout.addWidget(self.exportButton,0,xpos)
        xpos+=1                
        self.lineAction.setLayout(lineActionLayout)
        self.resultSetZone  = QtGui.QTableView()
        
        
        
        self.layout = QtGui.QGridLayout()
        self.layout.addWidget(self.editableZone,0,0)
        self.layout.addWidget(self.lineAction,1,0)
        self.layout.addWidget(self.resultSetZone,2,0)        
        self.layout.addWidget(self.resultCount,3,0)
        
        
        self.editableZone.setPlainText(sql)
        from dbexplorer.client import syntax       
        highlight = syntax.PythonHighlighter(self.editableZone.document())    
        self.setLayout(self.layout)
        
            
    def executeQuery(self):
        sql = self.editableZone.toPlainText()
        result = self.service.executeCustomSQL(self.datasourceId,sql)
        error = result['error']
                

        if error:
            (errorCode,errorMsg) = error.orig
            msg = QtGui.QMessageBox()
            msg.setText(errorMsg)
            msg.setIcon(QtGui.QMessageBox.Information)
            msg.exec_()
            return
        
        
        columnsName = result['columnsName']
        resultset = result['resultset']    
        self.resultCount.setText(_(u"%d résultat(s)")%(len(resultset)))
        
        model = CustomModel(resultset,columnsName)  
        
        self.resultSetZone.setModel(model)
        
        verticalHeader = self.resultSetZone.verticalHeader()
        verticalHeader.setMinimumSectionSize (self.view.fontsize+6)
        verticalHeader.setDefaultSectionSize(self.view.fontsize+6)
        self.resultSetZone.resizeColumnsToContents()
        
        
    def exportQuery(self):
        sql = self.editableZone.toPlainText()
        result = self.service.executeCustomSQL(self.datasourceId,sql)
        error = result['error']
                

        if error:
            (errorCode,errorMsg) = error.orig
            msg = QtGui.QMessageBox()
            msg.setText(errorMsg)
            msg.setIcon(QtGui.QMessageBox.Information)
            msg.exec_()
            return
        
        
        columnsName = result['columnsName']
        resultset = result['resultset']    
        
        
        fileName, filtr = QtGui.QFileDialog.getSaveFileName(self,_(u"Exportation"),_(u'monexport.csv'),_("All Files (*);;Text Files (*.txt)"))
    
        if fileName:
            sql = self.editableZone.toPlainText()
            result = self.service.exportCustomSQLToCsv(self.datasourceId,sql,fileName)
                                
            
        
        
class CustomModel(QtCore.QAbstractTableModel):
    def __init__(self,resultset,columnsName):
        QtCore.QAbstractTableModel.__init__(self)
        self.resultset = resultset
        self.columnsName = columnsName
        
        
    def rowCount(self, parent=QtCore.QModelIndex()):        
        return len(self.resultset)    
    
    def columnCount(self, parent=QtCore.QModelIndex()):        
        return len(self.columnsName)
    
    
    def headerData(self,section, orientation, role=QtCore.Qt.DisplayRole):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.columnsName[section]
        else :
            return QtCore.QAbstractTableModel.headerData(self,section, orientation, role)
        
    def data(self,index, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:
            row = index.row()
            column = index.column()
            return self.resultset[row][column]
   