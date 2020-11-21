# -*- coding: utf-8 -*-
#
"""
.. module:: burt
   :synopsis: module de génération du graphique de burt 
.. codeauthor:: pireh, amérique du nord, laurent frobert
"""
import sys
from PySide import QtCore, QtGui
from ProxyModelWithHeaderModels import ProxyModelWithHeaderModels
from HierarchicalHeaderView import HierarchicalHeaderView

class BurtModel(QtCore.QAbstractTableModel):
    def __init__(self,matrix):
        QtCore.QAbstractTableModel.__init__(self)
        self.matrix = matrix
        
    def rowCount(self, parent=QtCore.QModelIndex()):        
        return len(self.matrix)    
    
    def columnCount(self, parent=QtCore.QModelIndex()):        
        return len(self.matrix)
    
    def data(self,index, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:
            row = index.row()
            column = index.column()
            return unicode(self.matrix[row][column])
    
        
class BurtGraphe(QtGui.QDialog):
    def __init__(self,tablesView):
        QtGui.QDialog.__init__(self)
        self.tablesView = tablesView
        self.layout = QtGui.QVBoxLayout()
        self.setLayout(self.layout)
        self.resize(800,600)
        self.tv = QtGui.QTableView()
        self.tv.setWordWrap(False)
        self.layout.addWidget(self.tv)
        
        self.exportButton = QtGui.QPushButton(_(u'export CSV'))
        self.exportButton.setMaximumWidth(100)
        self.exportButton.clicked.connect(self.exportcsv)
        
        copyButton = QtGui.QPushButton(_(u"copy to clipboard"))
        copyButton.clicked.connect(self.copyToClipboard)
        
        self.bar = QtGui.QWidget()
        barLayout = QtGui.QGridLayout()
        barLayout.setContentsMargins(0,0,0,0)
        self.bar.setLayout(barLayout)
        
        barLayout.addWidget(self.exportButton,0,0)
        barLayout.addWidget(copyButton,0,1)
        
        self.layout.addWidget(self.bar)
        
    def draw(self,values,modalites,nomColonnes):
        self.values = values
        self.modalites = modalites
        self.nomColonnes = nomColonnes
        
        headerModel = QtGui.QStandardItemModel()
        
        self.BuildHeaderModel(headerModel)
        
        
        self.newmatrix = self.flattenMatrix()
        
        
        dataModel = BurtModel(self.newmatrix)
        
        
        model=ProxyModelWithHeaderModels()
        model.setModel(dataModel)
        model.setHorizontalHeaderModel(headerModel)
        model.setVerticalHeaderModel(headerModel)
        
            
        self.tv.setHorizontalHeader(HierarchicalHeaderView(QtCore.Qt.Horizontal,self.tv));
        self.tv.setVerticalHeader(HierarchicalHeaderView(QtCore.Qt.Vertical, self.tv));
        self.tv.setModel(model)
        
        verticalHeader = self.tv.verticalHeader()
        verticalHeader.setMinimumSectionSize (self.tablesView.tab.view.fontsize+6)
        verticalHeader.setDefaultSectionSize(self.tablesView.tab.view.fontsize+6)        
        self.tv.resizeColumnsToContents()
        
    def textSizeHasChanged(self,newsize):
        
        verticalHeader = self.tv.verticalHeader()
        verticalHeader.setMinimumSectionSize (newsize+6)
        verticalHeader.setDefaultSectionSize(newsize+6)        
        self.tv.resizeColumnsToContents()
    
    def exportcsv(self):
        from PySide.QtGui import QFileDialog
        fileName, filtr = QFileDialog.getSaveFileName(self,_(u"Exportation"),_(u'monexport.csv'),_("All Files (*);;Text Files (*.txt)"))
    
        if fileName:
            
            import dbexplorer.client.ucsv as csv            
            with open(fileName, 'wb') as outfile:        
                outcsv = csv.writer(outfile)
                
                h=['']        
                for nomCol in self.nomColonnes:        
                    for mod in self.modalites[nomCol]:
                        h.append("%s/%s"%(nomCol,mod))
                                
                outcsv.writerow(h)
                
                index = 1
                for row in self.newmatrix:
                    u=[h[index]] 
                    index += 1
                    for col in row:
                        u.append(col)
                    outcsv.writerow(u)
                
                
                
                outfile.flush()
                outfile.close()
                outfile = None
    
        
    def copyToClipboard(self):        
        clipboard = QtGui.QApplication.clipboard()        
        h=['']        
        for nomCol in self.nomColonnes:        
            for mod in self.modalites[nomCol]:
                h.append("%s/%s"%(nomCol,mod))
        t=[]                
        t.append('\t'.join(h))
        index = 1
        for row in self.newmatrix:
            u=[h[index]] 
            index += 1
            for col in row:
                u.append(col)
            t.append('\t'.join(u))
        clipboard.setText('\n'.join(t), QtGui.QClipboard.Clipboard)
            
    def BuildDataModel(self,model,matrix):
        
        for i in range(len(matrix)):
            l=[]            
            for j in range(len(matrix)):
                cell=QtGui.QStandardItem(unicode(matrix[i][j]))
                l.append(cell)
            model.appendRow(l)

    def flattenMatrix(self):
        sum_modalites = 0
        for m in self.modalites:
            sum_modalites += len(self.modalites[m])

         
        
        coords=[]
        for nomCol in self.nomColonnes:        
            for mod in self.modalites[nomCol]:
                coords.append((nomCol,mod))
        
        
        
        newmatrix = [ [ '-' for i in xrange(len(coords)) ] for j in xrange(len(coords)) ]
        
        for x in xrange(len(coords)):
            for y in xrange(len(coords)):
                if (coords[x],coords[y]) in self.values:
                    newmatrix[y][x] = unicode(self.values[(coords[x],coords[y])])
                elif (coords[y],coords[x]) in self.values:
                    newmatrix[y][x] = unicode(self.values[(coords[y],coords[x])])
                else:
                    newmatrix[y][x] = '-'
                    
        return newmatrix
        
    def BuildHeaderModel(self,headerModel):    
        x=0
        for nomCol in self.nomColonnes:
            cell=QtGui.QStandardItem(nomCol)  
            for modal in self.modalites[nomCol]:                
                if modal is None:
                    modal = _(u'vide')
                    
                if isinstance(modal,unicode) or isinstance(modal,str):
                    try:
                        u = unicode(modal)
                    except:
                        try:
                            u = unicode(modal,'utf8')
                        except:
                            u = modal
                    
                    
                    cell.appendColumn([QtGui.QStandardItem(u)])
                else:
                    cell.appendColumn([QtGui.QStandardItem(modal)])
                    
            headerModel.setItem(0, x, cell)
            x += 1
    
    
