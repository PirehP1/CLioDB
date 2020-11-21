# -*- coding: utf-8 -*-
"""
.. module:: tables
   :synopsis: Module d'affichage des différents graphes  
.. codeauthor:: pireh, amérique du nord, laurent frobert
"""
import os

import matplotlib
iconPrefix = './img/'
from PySide import QtCore, QtGui, QtWebKit
from burt import BurtGraphe       
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import pandas
#from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as _NavigationToolbar
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as _NavigationToolbar
from PySide.QtGui import QWidget, QVBoxLayout, QApplication, QCursor 
from matplotlib.backends.backend_qt4 import cursord 
from dbexplorer.client import syntax

class NavigationToolbar(_NavigationToolbar): 
    def set_cursor( self, cursor ): 
        QApplication.restoreOverrideCursor() 
        qcursor = QCursor() 
        qcursor.setShape(cursord[cursor]) 
        QApplication.setOverrideCursor( qcursor ) 


import numpy as np
iconPrefix = './img/'


from hierarchical_clustering import HierarchyGraphe


class Table(QtGui.QWidget):
    def __init__(self,name,index,tablesView,parent=None,iconName=None):        
        QtGui.QWidget.__init__(self,parent=parent)
        self.tablesView = tablesView
        self.index = index                
        self.button = QtGui.QRadioButton(name)           
        layout = QtGui.QGridLayout()
        layout.addWidget(self.button)
        self.setLayout(layout)
        self.button.clicked.connect(self.goto)
        
    def goto(self):
        
        currentIndex = self.tablesView.topTable.currentIndex()
        
        
        if currentIndex == self.index:
            pass
        
        self.tablesView.showSqlButton.hide()
        self.tablesView.diagonalisationCheck.hide()
        self.tablesView.exportButton.hide()
        self.tablesView.exportButtonPhi.hide()
        
        self.tablesView.tables[currentIndex].button.setChecked(False)
        
        
        if self.index == 0:
            pass
        elif self.index == 1:
            self.tablesView.diagonalisationCheck.show()
            self.tablesView.exportButtonPhi.show()                        
            pass
        elif self.index == 2:            
            pass
        elif self.index == 3:
            pass
        
        
        
        
        
        self.tablesView.topTable.setCurrentIndex(self.index)
        self.tablesView.bottomTable.setModel(None)
    
class TablesView(QtGui.QWidget):
    def __init__(self,tab,parent=None):
        QtGui.QWidget.__init__(self,parent=parent)
        self.tab = tab
        self.topTable = QtGui.QStackedWidget()
        self.topTables = []
        w1 = QtGui.QWidget()
        w1.setLayout(QtGui.QGridLayout()) #to replaced by the matplotlib plot
        w2 = QtGui.QWidget()
        w2.setLayout(QtGui.QGridLayout()) #to replaced by the matplotlib plot
        self.topTables.append(w1) 
        self.tableauB = TableauB(self)
        
        self.topTables.append(self.tableauB)
        self.burtGraphe = BurtGraphe(self)
        self.topTables.append(self.burtGraphe)
        self.topTables.append(w2)
        
        for w in self.topTables:
            self.topTable.addWidget(w)
        
        
        self.bar = QtGui.QWidget()
        barLayout = QtGui.QGridLayout()
        barLayout.setContentsMargins(0,0,0,0)
        self.bar.setLayout(barLayout)
        
        self.sqlView = QtGui.QPlainTextEdit()
        self.sqlViewIsOpen = False
        self.sqlViewPosition = None
        self.sqlView.setWindowTitle(_(u"Vue SQL"))        
        self.sqlView.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint) 
        highlight = syntax.PythonHighlighter(self.sqlView.document())
        
        self.showSqlButton = QtGui.QPushButton(_(u"vue SQL"))
        self.showSqlButton.setMaximumWidth(100)        
        self.showSqlButton.clicked.connect(self.openHideSqlView)
        
        
        self.exportButton = QtGui.QPushButton(_(u'export CSV'))
        self.exportButton.setMaximumWidth(100)
        self.exportButton.clicked.connect(self.exportcsv)
        
        self.diagonalisationCheck = QtGui.QCheckBox(_(u'diagonalisation'))
        self.diagonalisationCheck.setMaximumWidth(150)
        self.diagonalisationCheck.clicked.connect(self.diagonalisation)
        
        self.exportButtonPhi = QtGui.QPushButton(_(u'export CSV Phi2'))
        self.exportButtonPhi.setMaximumWidth(100)
        self.exportButtonPhi.clicked.connect(self.exportcsvphi)
        
        self.showSqlButton.hide()
        self.exportButton.hide()        
        self.diagonalisationCheck.hide()
        self.exportButtonPhi.hide()
        
        self.spacer = QtGui.QSpacerItem(1,1) 
        
        
        barLayout.addWidget(self.showSqlButton,0,0)
        barLayout.addWidget(self.exportButton,0,1)
        barLayout.addWidget(self.diagonalisationCheck,0,2)
        barLayout.addWidget(self.exportButtonPhi,0,3)
        barLayout.addItem(self.spacer,0,4)
        
        self.bottomTable = QtGui.QTableView()
        self.bottomTable.setWordWrap(False)
        
        self.bottomTable.setAlternatingRowColors(True) 
        
        self.bottom = QtGui.QWidget()
        bottomLayout = QtGui.QGridLayout()
        bottomLayout.setContentsMargins(0,0,0,0)
        self.bottom.setLayout(bottomLayout)
        bottomLayout.addWidget(self.bar)
        bottomLayout.addWidget(self.bottomTable)
        
        self.tables = []
        self.tables.append(Table(_(u'Tableau Quantitatif'),0,self,iconName='tableauA-quantitatif-3.png')) #tableau A
        self.tables.append(Table(_(u'Tableau Qualitatif'),1,self,iconName='tableauB-qualitatif-3.png')) #tableau B
        self.tables.append(Table(_(u'Tableau Burt'),2,self)) #tableau C
        self.tables.append(Table(_(u'Graphique du\ntableau\ndes modalités\nréordonné'),3,self)) #tableau C
                
        self.returnButton = QtGui.QPushButton(_(u'retour explo'))
        
        self.tablesZone = QtGui.QWidget()
        tablesZoneLayout = QtGui.QGridLayout()
        tablesZoneLayout.setContentsMargins(0,0,0,0)
        self.tablesZone.setLayout(tablesZoneLayout)
        
        for w in self.tables:
            tablesZoneLayout.addWidget(w)
        
        tablesZoneLayout.addWidget(self.returnButton)
        self.returnButton.clicked.connect(self.retourExplo)
        
        
        self.splitterV = QtGui.QSplitter(QtCore.Qt.Vertical)
        self.splitterV.setContentsMargins(0,0,0,0)
        self.splitterV.addWidget(self.topTable)
        self.splitterV.addWidget(self.bottom)
        
        
        self.splitterH = QtGui.QSplitter(QtCore.Qt.Horizontal)
        self.splitterH.setContentsMargins(0,0,0,0)
        self.splitterH.addWidget(self.splitterV)
        self.splitterH.addWidget(self.tablesZone)
        
        myLayout = QtGui.QGridLayout()
        myLayout.setContentsMargins(0,0,0,0)
        self.setLayout(myLayout)
        myLayout.addWidget(self.splitterH)
        
        
    def textSizeHasChanged(self,newsize):
        verticalHeader = self.tableauB.verticalHeader()
        verticalHeader.setMinimumSectionSize (newsize+6)
        verticalHeader.setDefaultSectionSize(newsize+6)        
        self.tableauB.resizeColumnsToContents()
        '''
        self.tableauB.resizeColumnsToContents()
        self.tableauB.resizeRowsToContents()
        self.tableauB.verticalHeader().setResizeMode(QtGui.QHeaderView.Stretch)
        '''
        
        self.burtGraphe.textSizeHasChanged(newsize)
        
        verticalHeader = self.bottomTable.verticalHeader()
        verticalHeader.setMinimumSectionSize (newsize+6)
        verticalHeader.setDefaultSectionSize(newsize+6)        
        self.bottomTable.resizeColumnsToContents()
        '''
        self.bottomTable.resizeColumnsToContents()
        self.bottomTable.resizeRowsToContents()
        self.bottomTable.verticalHeader().setResizeMode(QtGui.QHeaderView.Stretch)
        ''' 
                
    def openHideSqlView(self):
        if self.sqlView.isVisible():
            #self.sqlViewPosition = self.sqlView.pos()
            self.sqlViewPosition = self.sqlView.saveGeometry() 
            self.sqlView.hide()
            self.sqlViewIsOpen = False
        else:            
            self.sqlView.show()
            if self.sqlViewPosition:
                self.sqlView.restoreGeometry(self.sqlViewPosition)
                #self.sqlView.move(self.sqlViewPosition)
            self.sqlViewIsOpen = True
    
    def exportcsvphi(self):
        from PySide.QtGui import QFileDialog
        fileName, filtr = QFileDialog.getSaveFileName(self,_(u"Exportation"),_(u'monexport.csv'),_("All Files (*);;Text Files (*.txt)"))
    
        if fileName:
            model = self.tableauB.model()
            rows = model.rowCount()
            cols = model.columnCount()
            
            import dbexplorer.client.ucsv as csv            
            with open(fileName, 'wb') as outfile:        
                outcsv = csv.writer(outfile)
                headers=['']
                for i in range(0,cols):
                    headers.append(model.headerData(i,QtCore.Qt.Horizontal))
                outcsv.writerow(headers)
                
                for r in range(0,rows):
                    row = [model.headerData(r,QtCore.Qt.Vertical)]
                    for c in range(0,cols):                    
                        index = model.index(r,c,QtCore.QModelIndex())
                        val = model.data(index)
                        if val is None:
                            row.append('')
                        else:
                            row.append(val)
                    outcsv.writerow(row)
                # or maybe use outcsv.writerows(records)
                outfile.flush()
                outfile.close()
                outfile = None
        
    def exportcsv(self):        
        if self.bottomTable.model() is None:
            return
        
        from PySide.QtGui import QFileDialog
        fileName, filtr = QFileDialog.getSaveFileName(self,_(u"Exportation"),_(u'monexport.csv'),_("All Files (*);;Text Files (*.txt)"))
    
        if fileName:
            model = self.bottomTable.model()
            rows = model.rowCount()
            cols = model.columnCount()
            
            import dbexplorer.client.ucsv as csv            
            with open(fileName, 'wb') as outfile:        
                outcsv = csv.writer(outfile)
                headers=[]
                for i in range(0,cols):
                    headers.append(model.headerData(i,QtCore.Qt.Horizontal))
                outcsv.writerow(headers)
                
                for r in range(0,rows):
                    row = []
                    for c in range(0,cols):                    
                        index = model.index(r,c,QtCore.QModelIndex())
                        val = model.data(index)
                        if val is None:
                            row.append('')
                        else:
                            row.append(val)
                    outcsv.writerow(row)
                # or maybe use outcsv.writerows(records)
                outfile.flush()
                outfile.close()
                outfile = None
            
            
            
    
    def diagonalisation(self):        
        self.tableauB.diag(self.diagonalisationCheck.isChecked())
            
    def retourExplo(self):
        self.tab.stackedTab.setCurrentIndex(0)
    
    def isExcluded(self,tables,f,model):                
        for m in model:
            [(tableItem,columnItem),type,qualificatif,exclus]  = m
            if self.tab.findColumnItem(f['tableId'],f['column']) == columnItem :
                if exclus is True:
                    return True
                else:
                    return qualificatif
            
        return False
    
    """
    def getIndexOfMod(self,nomCol,mod,tab):
        for i in range(len(tab)):            
            if tab[i]['column'] == nomCol and tab[i]['modalite'] == mod:
                return i        
    """
            
    def findTableId(self,nomcol,sc):
        for s in sc:
            if s['column'] == nomcol:
                return s['tableId']
        return None
    """
    def getFiltreSubDomain_1(self,subdomain,sc):
        ands=['ET']
        for nomcol in subdomain:            
            tableId = self.findTableId(nomcol,sc)
            domain = subdomain[nomcol]
            ors = ['OU']
            for val in domain:                
                if val=='None':
                    nullable = True
                else:
                    nullable = False
                    
                if val=='':
                    empty=True
                else:
                    empty = False    
                
                if nullable:
                    val=None    
                ors.append([tableId,nomcol,u'=',-1,val,{u'null':nullable,u'empty':empty}])
                
            ands.append(ors)
    """
    def getAttribVal(self,currentVal):
        if currentVal=='None':
            currentNullable = True
        else:
            currentNullable = False
            
        if currentVal=='':
            currentEmpty=True
        else:
            currentEmpty = False    
        
        if currentNullable:
            currentVal=None
        '''
        if isinstance(currentVal,basestring):
            currentVal = unicode(currentVal.encode("utf-8"))
        '''    
        return currentVal,currentNullable , currentEmpty
              
    def getFiltreSubDomain_3(self,subdomainx,subdomainy,sc):
        globalfiltre=['OU']
        for y in subdomainy:
            yNomCol, yVal = y 
            yTableId = self.findTableId(yNomCol,sc)
            yVal,yNullable,yEmpty = self.getAttribVal(yVal)
            
            for x in subdomainx:
                ands = ['ET']
                ands.append([yTableId,yNomCol,u'=',-1,yVal,{u'null':yNullable,u'empty':yEmpty}])
                
                xNomCol, xVal = x 
                xTableId = self.findTableId(xNomCol,sc)
                xVal,xNullable,xEmpty = self.getAttribVal(xVal)
                ands.append([xTableId,xNomCol,u'=',-1,xVal,{u'null':xNullable,u'empty':xEmpty}])
                globalfiltre.append(ands)
                
        return globalfiltre
    
    def getFiltreSubDomain_2(self,subdomain,sc):
        #print "subdomain=",subdomain
        globalfiltre=['OU']
        
        from copy import deepcopy
        subdomain_copy = deepcopy(subdomain)
        
        while len(subdomain_copy)>1:
            currentNomCol, currentDomain = subdomain_copy.popitem() 
            currentTableId = self.findTableId(currentNomCol,sc)
            
            for currentVal in currentDomain:
                if currentVal=='None':
                    currentNullable = True
                else:
                    currentNullable = False
                    
                if currentVal=='':
                    currentEmpty=True
                else:
                    currentEmpty = False    
                
                if currentNullable:
                    currentVal=None
                
                ands = ['ET']
                ands.append([currentTableId,currentNomCol,u'=',-1,currentVal,{u'null':currentNullable,u'empty':currentEmpty}])
                    
                for nomcol in subdomain_copy:            
                    tableId = self.findTableId(nomcol,sc)
                    domain = subdomain_copy[nomcol]
                    ors = ['OU']
                    for val in domain:                
                        if val=='None':
                            nullable = True
                        else:
                            nullable = False
                            
                        if val=='':
                            empty=True
                        else:
                            empty = False    
                        
                        if nullable:
                            val=None    
                        ors.append([tableId,nomcol,u'=',-1,val,{u'null':nullable,u'empty':empty}])
                                                        
                    ands.append(ors)
                
                globalfiltre.append(ands)
            
        return globalfiltre
            
    def showSubDomain(self,subdomainx,subdomainy):        
        (tables,joins,sc,filtre)  = self.tab.buildQuery()
        
        filt = self.getFiltreSubDomain_3(subdomainx,subdomainy,sc)
        
                
        try:
            
            if filtre is not None:
                filt2 = ['ET',filt]
                if filtre[0] == '??':
                    filt2.append(filtre[1])
                else:
                    filt2.append(filtre) 
                filt = filt2
                
            newfilter = filt
            
            result = self.tab.service.executeQuery(self.tab.datasourceId,tables,joins,sc,newfilter,None,None)
            
            sql = result['query']
            sql = sql.replace('SELECT','SELECT\n').replace('JOIN','\nJOIN').replace(' ON ','\n    ON ')
            sql = sql.replace(',',',\n').replace('WHERE','WHERE\n').replace("LEFT OUTER","\nLEFT OUTER")
            sql = sql.replace("GROUP BY","\nGROUP BY").replace("ORDER BY","\nORDER BY")
            
            self.sqlView.setPlainText(sql)            
            self.showSqlButton.show()
            self.exportButton.show()
            
            columnsName = result['header']
            
            resultset = result['resultset']    
            from customsql import CustomModel
            model = CustomModel(resultset,columnsName)  
        
            self.bottomTable.setModel(model) 
            '''
            self.bottomTable.resizeColumnsToContents()
            self.bottomTable.resizeRowsToContents()
            self.bottomTable.verticalHeader().setResizeMode(QtGui.QHeaderView.Stretch)
            '''
            verticalHeader = self.bottomTable.verticalHeader()
            verticalHeader.setMinimumSectionSize (self.tab.view.fontsize+6)
            verticalHeader.setDefaultSectionSize(self.tab.view.fontsize+6)        
            self.bottomTable.resizeColumnsToContents()
        except Exception as e:
            import sys
            print sys.exc_info()
            

        
    def setModel(self,model):
        #pour info : model = [ [(tableItem,columnItem),type,qualificatif,exclus], ...]
        self.bottomTable.setModel(None)
        
        # calcul du tableau de burt
        (tables,joins,sc,filtre)  = self.tab.buildQuery()  
        newsc = []
        qualificatif=[] #todo renommer cette variable : en "qualifiant" (car = Quantitatif ou qualitatif)
        for f in sc: #f = (tableItem,columnItem,other) 
            isExcludedOrQualificatif = self.isExcluded(tables,f,model)
            if isExcludedOrQualificatif is not True:                            
                f['newname'] = f['column']                                
                newsc.append(f)                
                qualificatif.append(isExcludedOrQualificatif)
        
                                    
        burtviewIndex = 2        
        
        response2 = self.tab.service.getBurt(self.tab.datasourceId,tables,joins,newsc,filtre)
        
        
        self.topTables[burtviewIndex].draw(response2['values'],response2['modalites'],response2['nomColonnes'])
        
        hierarchyClusterIndex = 3
        
        if hasattr(self, "main_widget_hierarchy"):
            self.topTables[hierarchyClusterIndex].layout().removeWidget(self.main_widget_hierarchy)
            self.main_widget_hierarchy.hide()
            del self.main_widget_hierarchy
        
        
        import hierarchical_clustering
        matrix, row_header, column_header = hierarchical_clustering.toMatrix(response2['values'],response2['modalites'],response2['nomColonnes'])
        fig,new_row_header,new_column_header = hierarchical_clustering.plot(matrix, row_header, column_header,self)
        self.main_widget_hierarchy = HierarchyGraphe(matrix, row_header, column_header,self,fig,new_row_header,new_column_header)
        
        
        
        self.topTables[hierarchyClusterIndex].layout().addWidget(self.main_widget_hierarchy)
        
            
        scatterviewIndex = 0
        
        #------ calcul dataframe qualitatif
        newsc3=[]
        for i in range(len(newsc)):
            if qualificatif[i] == 'Qualitatif':
                newsc3.append(newsc[i])
            
        if len(newsc3)>0:
            dataframeQuali = self.tab.service.getDataframe(self.tab.datasourceId,tables,joins,newsc3,filtre)
            
            dataframeQualiWithPhi2 = self.tab.service.computeDataFramePhi2(dataframeQuali)
            
            self.tableauB.setDataframeQuali(dataframeQuali)
            
            #sums = np.nansum(dataframeQualiWithPhi2.values,axis=0)
            
            sums = dataframeQualiWithPhi2.values.sum(axis=0) 
            
            newindex = [i[0] for i in sorted(enumerate(sums), key=lambda x:x[1],reverse=True)]
            
            reindex = map(lambda x:dataframeQualiWithPhi2.columns[x],newindex)
            
            self.tableauB.dataframeDiag = dataframeQualiWithPhi2.reindex(index=reindex,columns=reindex)
        
            self.tableauB.dataframeNonDiag = dataframeQualiWithPhi2
            
            
            self.tableauB.setModel(DataFrameModel(dataframeQualiWithPhi2,dataframeQualiWithPhi2.columns,hideIntersec=True))
            '''
            self.tableauB.resizeColumnsToContents()
            self.tableauB.resizeRowsToContents()
            self.tableauB.verticalHeader().setResizeMode(QtGui.QHeaderView.Stretch)
            '''
            verticalHeader = self.tableauB.verticalHeader()
            verticalHeader.setMinimumSectionSize (self.tab.view.fontsize+6)
            verticalHeader.setDefaultSectionSize(self.tab.view.fontsize+6)        
            self.tableauB.resizeColumnsToContents()
        #------
        
        newsc2=[]
        for i in range(len(newsc)):
            if qualificatif[i] == 'Quantitatif':
                newsc2.append(newsc[i])
        
        
        if hasattr(self, "main_widget_sac"):
            self.topTables[scatterviewIndex].layout().removeWidget(self.main_widget_sac)
            self.main_widget_sac.hide()
            del self.main_widget_sac
               
             
        if len(newsc2) >=2: #minimum 2 fields to compute and plot the graph                                
            self.main_widget_sac = QtGui.QWidget(self)
            # create a vertical box layout widget
            vbl = QtGui.QVBoxLayout(self.main_widget_sac)
            # instantiate our Matplotlib canvas widget
            
            data,names,types = self.tab.service.getDataScatterPlot(self.tab.datasourceId,tables,joins,newsc2,filtre)
            
            
            qmc = NewScatterPlot(self,data,names,types) 
            
            
            # instantiate the navigation toolbar
            ntb = NavigationToolbarScatterPlot(qmc, self.main_widget_sac)
            # pack these widget into the vertical box
            vbl.addWidget(qmc)
            vbl.addWidget(ntb)
        
        #----
        
        
        if hasattr(self, "main_widget_sac"):       
            self.topTables[scatterviewIndex].layout().addWidget(self.main_widget_sac)
            currentIndex = scatterviewIndex
        else:
            currentIndex = 1
            self.diagonalisationCheck.show()
            self.exportButtonPhi.show()
            
        self.topTable.setCurrentIndex(currentIndex)
        
        
            
        
        for i in range(0,len(self.tables)):
            self.tables[i].button.setChecked(False)
             
        self.tables[currentIndex].button.setChecked(True)
        
    
        
    '''    
    def computeDataFramePhi2(self,dataf):
        
        dataframe = dataf.fillna(0)    
          
        index = columns = dataframe.columns
        df = pandas.DataFrame(index=index, columns=columns)
        
        df = df.fillna(0) # with 0s rather than NaN (init)
        
        
        for x in xrange(len(index)):
            for y in xrange(x,len(index)):
                phi2 = self.get_phi2(dataframe, index[x], index[y])
                df[index[x]][index[y]] = phi2
                df[index[y]][index[x]] = phi2
        
            
        return df

    def get_phi2(self,df,index1,index2):
        if index1 == index2:
            N = np.count_nonzero(df[index1].unique())            
            #N = len([dfwithnan[index1].unique()])            
            return N
            
        
        array = pandas.crosstab(df[index1],df[index2]).values
        sum_cols = array.sum(axis=0)
        sum_rows = array.sum(axis=1)
        N        = array.sum()
                
        
        chi2 = 0.0
        (num_row, num_col) = np.shape(array)
        for i in xrange(num_row):
            for j in xrange(num_col):
                observation = array[i,j]
                expectation = 1.0 * sum_rows[i] * sum_cols[j] / N
                chi2 += 1.0 * (observation - expectation) ** 2 / expectation
                
        return chi2/N
    '''
class Bertin(FigureCanvas):
    def __init__(self,dataframe):
        values = dataframe.values
        
        
        my_cmap_old = matplotlib.colors.LinearSegmentedColormap.from_list('my_colormap',
                                           ['white','blue'],
                                           len(values))
                
        xx = plt.matshow(values,cmap=my_cmap_old) #'cool'
        plt.xticks(range(len(dataframe.columns)), dataframe.columns, rotation=90)
        plt.yticks(range(len(dataframe.index)), dataframe.index)        
        fig = xx.get_figure()
        
        FigureCanvas.__init__(self,fig)
        
    def cmap_discretize(self,cmap, N):            
        colors_i = np.concatenate((np.linspace(0, 1., N), (0.,0.,0.,0.))) 
        colors_rgba = cmap(colors_i)
        indices = np.linspace(0, 1., N+1)
        cdict = {}
        for ki,key in enumerate(('red','green','blue')):
            cdict[key] = [ (indices[i], colors_rgba[i-1,ki], colors_rgba[i,ki]) for i in xrange(N+1) ]
        # Return colormap object.
        return matplotlib.colors.LinearSegmentedColormap(cmap.name + "_%d"%N, cdict, 1024)

class NewScatterPlot(FigureCanvas):
    def __init__(self,tablesView,data,names,types):
        self.tablesView = tablesView
        self.data = data
        self.names = names
        self.types = types
            
        
        datacopy = np.copy(data)
        self.fig = self.scatterplot_matrix(datacopy, names, types,linestyle='none',marker='.', alpha=0.2)
        
        self.fig.subplots_adjust(wspace=0.2, hspace=0.2)
        self.oldGeometry = None
        self.oldAxe = None
        FigureCanvas.__init__(self,self.fig)
        
        def onclick(event):
            if self.oldAxe is not None:
                return
            
            col1= event.inaxes.get_xlabel()
            col2 = event.inaxes.get_ylabel()
            
            if col1=='' or col2=='': #click on column name (diagonal plot)
                return
             
            axes = self.fig.get_axes()
            for axe in axes:
                axe.set_visible(False)
                
            event.inaxes.set_visible(True)
            
            self.oldAxeX_visible = event.inaxes.xaxis._visible
            self.oldAxeY_visible = event.inaxes.yaxis._visible
            event.inaxes.xaxis.set_visible(True)
            event.inaxes.yaxis.set_visible(True)
            
            
            self.oldGeometry = event.inaxes.get_geometry()            
            self.oldAxe = event.inaxes
            
            event.inaxes.change_geometry(1,1,1)
             
            self.fig.canvas.draw() 
            
            i1 = self.names.index(col1)
            i2 = self.names.index(col2)
            
            dataframe = pandas.DataFrame({col1:self.data[i1],col2:self.data[i2]})
                        
            
            model = DataFrameModel(dataframe,[col1,col2],False,[self.types[i1],self.types[i2]])
        
            self.tablesView.bottomTable.setModel(model)
            ''' 
            self.tablesView.bottomTable.resizeColumnsToContents()
            self.tablesView.bottomTable.resizeRowsToContents()
            self.tablesView.bottomTable.verticalHeader().setResizeMode(QtGui.QHeaderView.Stretch)
            '''
            verticalHeader = self.tablesView.bottomTable.verticalHeader()
            verticalHeader.setMinimumSectionSize (self.tablesView.tab.view.fontsize+6)
            verticalHeader.setDefaultSectionSize(self.tablesView.tab.view.fontsize+6)        
            self.tablesView.bottomTable.resizeColumnsToContents()
            
            self.tablesView.exportButton.show()
            
        cid = self.mpl_connect('button_press_event', onclick)
        
    
    def scatterplot_matrix(self,data, names, types, **kwargs):                
        numvars, numdata = data.shape
        import matplotlib.dates as mdates
        
        for i in range(len(names)): #names
            if types[i] == 'date' or types[i] == 'datetime':
                data[i]=mdates.date2num(data[i])
                
        fig, axes = plt.subplots(nrows=numvars, ncols=numvars, figsize=(8,8))
        fig.subplots_adjust(hspace=0.05, wspace=0.05)
    
        
        #for ax in axes.flat:
        
        n = numvars
        for i, a in zip(range(numvars), names):
            for j, b in zip(range(numvars), names): 
                ax = axes[i, j]
                
                
                # Hide all ticks and labels
                ax.xaxis.set_visible(False) #False
                ax.yaxis.set_visible(False)
            
            
        for i, a in zip(range(numvars), names):
            for j, b in zip(range(numvars), names):
                if i==j:
                    continue
                
                
                axes[i,j].plot(data[j], data[i], **kwargs)
                axes[i,j].set_xlabel(names[j],visible=False)
                axes[i,j].set_ylabel(names[i],visible=False)
        
        n = numvars
        for i, a in zip(range(numvars), names):
            for j, b in zip(range(numvars), names): 
                if i==j:
                    continue                
                ax = axes[i, j]
                
                # Set up ticks only on one side for the "edge" subplots...
                if ax.is_first_col():
                    ax.yaxis.set_ticks_position('left')                    
                    ax.yaxis.set_visible(True)                    
                        
                if ax.is_last_col():
                    ax.yaxis.set_ticks_position('right')
                    ax.yaxis.set_visible(True)
                    
                if ax.is_first_row():
                    ax.xaxis.set_ticks_position('top')
                    ax.xaxis.set_visible(True)
                    
                    xlabels = ax.get_xticklabels()
                    for label in xlabels:
                        label.set_rotation(30)
                        label.set_ha('left')
                    
                if ax.is_last_row():
                    ax.xaxis.set_ticks_position('bottom')
                    ax.xaxis.set_visible(True)
                    
                    xlabels = ax.get_xticklabels()
                    for label in xlabels:
                        label.set_rotation(-30)
                        label.set_ha('left')
                                
        
        # Label the diagonal subplots...
        for i, label in enumerate(names):
            axes[i,i].annotate(label, (0.5, 0.5), xycoords='axes fraction',
                    ha='center', va='center')
        
        #from matplotlib.ticker import MaxNLocator
        for i, a in zip(range(numvars), names):
            for j, b in zip(range(numvars), names): 
                ax = axes[i, j]
                if i==j:
                    continue
                
                
                if types[i] == 'date' or types[i] == 'datetime':                    
                    dayspan = mdates.num2date(max(data[i])) - mdates.num2date(min(data[i]))
                    dayspan = dayspan.days
                    
                    if dayspan < 70:
                        ax.yaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
                    elif dayspan < 700:
                        ax.yaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
                    else:
                        ax.yaxis.set_major_formatter(mdates.DateFormatter('%Y'))
                                        
                    
                    ax.autoscale(enable=True, axis='y', tight=False)    
                        
                if types[j] == 'date' or types[j] == 'datetime':                    
                    dayspan = mdates.num2date(max(data[j])) - mdates.num2date(min(data[j]))
                    dayspan = dayspan.days
                    
                    if dayspan < 70:
                        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
                    elif dayspan < 700:
                        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
                    else:
                        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
                        
                    ax.autoscale(enable=True, axis='x', tight=False)        
                        
                             
        
        return fig

"""
class ScatterPlot(FigureCanvas):
    def __init__(self,tablesView,dataframe):
        self.tablesView = tablesView
        # Standard Matplotlib code to generate the plot
        self.dataframe = dataframe
        axes = pandas.tools.plotting.scatter_matrix(dataframe,alpha=0.2) #,figsize=(8, 8), diagonal='kde')
        n = dataframe.columns.size
        for i, a in zip(range(n), dataframe.columns):
            for j, b in zip(range(n), dataframe.columns):
                axes[i, j].set_xlabel(b)
                axes[i, j].set_ylabel(a)
                axes[i, j].xaxis.set_visible(False)
                axes[i, j].yaxis.set_visible(False)
                
                ax = axes[i,j] 
                
                if i == 0 :
                    ax.set_xlabel(b, visible=True)
                    ax.xaxis.set_visible(True)
                    ax.set_xlabel(b)
                    ax.xaxis.set_label_position('top')
                    if j % 2 == 0:
                        ax.xaxis.set_ticks_position('none')                        
                    else:
                        ax.xaxis.set_ticks_position('top')
                
                elif i == (n-1) :
                    ax.set_xlabel(b, visible=True)
                    ax.xaxis.set_visible(True)
                    ax.set_xlabel(b)
                    ax.xaxis.set_label_position('bottom')
                    if j % 2 == 1:
                        ax.xaxis.set_ticks_position('none')                        
                    else:
                        ax.xaxis.set_ticks_position('bottom')
                else:
                    ax.set_xlabel(b, visible=False)
                    ax.xaxis.set_visible(True)                                        
                    ax.xaxis.set_ticks_position('bottom')                        
                    
                    
                if j == 0 :
                    ax.set_ylabel(a, visible=True)
                    ax.yaxis.set_visible(True)
                    ax.set_ylabel(a)
                    ax.yaxis.set_label_position('left')
                    if i % 2 == 0:
                        ax.yaxis.set_ticks_position('none')                        
                    else:
                        ax.yaxis.set_ticks_position('left')                
                elif j == (n-1) :
                    ax.set_ylabel(a, visible=True)
                    ax.yaxis.set_visible(True)
                    ax.set_ylabel(a)
                    ax.yaxis.set_label_position('right')
                    if i % 2 == 1:
                        ax.yaxis.set_ticks_position('none')                        
                    else:
                        ax.yaxis.set_ticks_position('right')                
                else:
                    ax.set_ylabel(a, visible=False)
                    ax.yaxis.set_visible(True)                                        
                    ax.yaxis.set_ticks_position('left')
                                    
                                                
        fig = axes[0][0].get_figure()
        fig.subplots_adjust(wspace=0.2, hspace=0.2)
        
        FigureCanvas.__init__(self,fig)
        def onclick(event):                     
            col1= event.inaxes.get_xlabel()
            col2 = event.inaxes.get_ylabel()
            
            model = DataFrameModel(self.dataframe,[col1,col2])
        
            self.tablesView.bottomTable.setModel(model) 
            self.tablesView.bottomTable.resizeColumnsToContents()
            
        cid = self.mpl_connect('button_press_event', onclick)
        
"""
            
import simplejson as json
"""         
class BurtService(QtCore.QObject):
    def __init__(self,tableView):
        QtCore.QObject.__init__(self)        
        self.tableView = tableView
        
    @QtCore.Slot(str)
    def fieldSelected(self,fields_json):
        fields = json.loads(fields_json)        
        print fields
        

    
    def readDataset(self):
        return self.ppval
 
    def setDataset(self,val):
        self.ppval = val
        
    dataset = QtCore.Property(str, readDataset, setDataset)   
"""

"""            
class BurtView(QtGui.QWidget):
    def __init__(self,tableView):
        QtGui.QWidget.__init__(self)        
        self.layout  = QtGui.QGridLayout()
        self.setLayout(self.layout)
        self.tableView = tableView
        
    def render(self,datasets) :            
        self.datasets = datasets
        
        self.burtService = BurtService(self.tableView)
        
        try:
            if self.webView :
                self.layout.removeWidget(self.webView)
        except:
            pass
                
        self.webView = QtWebKit.QWebView()
        self.layout.addWidget(self.webView,0,0)
        
        
        self.webView.loadFinished.connect(self.loadFinished)
        self.webView.page().mainFrame().addToJavaScriptWindowObject("burtService", self.burtService)
        self.webView.load(QtCore.QUrl("./resources/burt.html"))
        

        
    def loadFinished(self):        
        self.burtService.dataset = self.datasets
        self.webView.page().mainFrame().evaluateJavaScript('drawChartFromPython()');
"""        

class DataFrameModel(QtCore.QAbstractTableModel):
    def __init__(self,dataframe,cols,margins=False,types=None,hideIntersec=False):
        QtCore.QAbstractTableModel.__init__(self)
        self.dataframe = dataframe
        self.cols=cols
        self.margins = margins
        self.types = types
        self.hideIntersec = hideIntersec
        
    def rowCount(self, *args, **kwargs):  
        if self.margins:
            d = 1
        else:
            d = 0
                  
        return len(self.dataframe.values) + d
    
    def columnCount(self,parent=QtCore.QModelIndex()):
        if self.margins:
            d = 1
        else:
            d = 0
        return len(self.cols) + d
    
    def flags(self,index):    
        return QtCore.Qt.ItemIsEnabled # | ~ QtCore.Qt.ItemIsEditable | ~QtCore.Qt.ItemIsSelectable
    
    
    def data(self,index, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:            
            row = index.row()
            col = index.column()
            
            if (row == col) and self.hideIntersec:
                return "--"
            
            if self.margins and (row == len(self.dataframe.values) or col == len(self.cols)):  
                if row == len(self.dataframe.values) and col != len(self.cols):
                    return "%s"%(np.sum(self.dataframe[self.cols[col]].values))
                elif row != len(self.dataframe.values) and col == len(self.cols):
                    return "%s"%(np.sum(self.dataframe[self.cols].values[row]))
                else :
                    return "%s"%(np.sum(self.dataframe[self.cols].values))
            else:    
                val = self.dataframe[self.cols[col]][self.dataframe.index[row]]
                          
                if val is None:
                    return None
                elif pandas.isnull(val):
                    return '---'
                else:                
                    if self.types is not None:
                        if self.types[col] == 'date':
                            return val.isoformat()[0:10]
                        elif self.types[col] == 'datetime':
                            return val.isoformat()
                                                
                    return '%s'%(val)
        
    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):        
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal :
                if self.margins and section == len(self.cols):
                    return 'All'
                else:
                    return '%s'%(self.cols[section])
            else:
                if self.margins and section == len(self.dataframe.values):
                    return 'All'
                else:                
                    return '%s'%(self.dataframe.index[section])
                
            
        return None

class TableauB(QtGui.QTableView):
    def __init__(self,tablesView,parent=None):
        QtGui.QTableView.__init__(self,parent=parent)
        self.tablesView = tablesView
        self.clicked.connect(self.showDetails)
        self.dataframeQuali = None
        
        self.dataframeNonDiag = None
        self.dataframeDiag = None
        self.setWordWrap(False)
        
        
    def setDataframeQuali(self,df):
        self.dataframeQuali = df
        
    def diag(self,isDiag):
        if not isDiag :
            self.setModel(DataFrameModel(self.dataframeNonDiag,self.dataframeNonDiag.columns,hideIntersec=True))
        else:
            self.setModel(DataFrameModel(self.dataframeDiag,self.dataframeDiag.columns,hideIntersec=True))
    
            
    def showDetails(self,index):
        row = index.row()
        col = index.column()
        cols = self.model().dataframe.columns
        
        
        if row == col:
            detailDF = pandas.DataFrame(self.dataframeQuali[cols[col]])
            detailDFBertin = detailDF
            margins = False
        else:
            v1 = self.dataframeQuali[cols[row]]
            v2 = self.dataframeQuali[cols[col]]
            detailDF = pandas.crosstab(v1,v2) #todo : le margins=True semble poser probleme avec les dates, donc faire le margins dans le model du tableview 
            
            detailDFBertin = detailDF
            margins = True
            
        
        self.tablesView.bottomTable.setModel(DataFrameModel(detailDF,detailDF.columns,margins=margins))
        ''' 
        self.tablesView.bottomTable.resizeColumnsToContents()
        self.tablesView.bottomTable.resizeRowsToContents()
        self.tablesView.bottomTable.verticalHeader().setResizeMode(QtGui.QHeaderView.Stretch)
        '''
        verticalHeader = self.tablesView.bottomTable.verticalHeader()
        verticalHeader.setMinimumSectionSize (self.tablesView.tab.view.fontsize+6)
        verticalHeader.setDefaultSectionSize(self.tablesView.tab.view.fontsize+6)        
        self.tablesView.bottomTable.resizeColumnsToContents()
        
        self.tablesView.exportButton.show()
        
        if row != col:
            self.modal = QtGui.QDialog()                
            # create a vertical box layout widget
            vbl = QtGui.QVBoxLayout()
            # instantiate our Matplotlib canvas widget
            qmc = Bertin(detailDFBertin)
            # instantiate the navigation toolbar
            ntb = NavigationToolbar(qmc, self.modal)
            # pack these widget into the vertical box
            vbl.addWidget(qmc)
            vbl.addWidget(ntb)                        
            self.modal.setLayout(vbl)
            self.modal.show()

        
                
        

class NavigationToolbarScatterPlot(_NavigationToolbar): 
    def __init__(self,canvas,parent):
        _NavigationToolbar.__init__(self, canvas, parent,coordinates=False)
        
        #self.toolitems = [t for t in self.toolitems if t[0] in ('Home', 'Save')]
        
    def set_cursor( self, cursor ): 
        QApplication.restoreOverrideCursor() 
        qcursor = QCursor() 
        qcursor.setShape(cursord[cursor]) 
        QApplication.setOverrideCursor( qcursor )
    
    def home(self):        
        if self.canvas.oldGeometry is None:
            return
        
        axes = self.canvas.fig.get_axes()
        for axe in axes:
            axe.set_visible(True)
        
        (a,b,c) = self.canvas.oldGeometry    
        self.canvas.oldAxe.change_geometry(a,b,c)
        
        self.canvas.oldAxe.xaxis.set_visible(self.canvas.oldAxeX_visible)
        self.canvas.oldAxe.yaxis.set_visible(self.canvas.oldAxeY_visible)
        
        self.canvas.oldAxe = None
        self.canvas.oldGeometry = None
        
            
        self.canvas.draw()
        
    def _init_toolbar(self):
        self.basedir = os.path.join(matplotlib.rcParams[ 'datapath' ],'images')

        a = self.addAction(self._icon('home.png'), 'Home', self.home)
        a.setToolTip('Reset original view')

        a = self.addAction(self._icon('filesave.png'), 'Save',
                self.save_figure)
        a.setToolTip('Save the figure')

        
