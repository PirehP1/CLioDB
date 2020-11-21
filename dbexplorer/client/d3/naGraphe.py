import sys
from PySide import QtCore, QtGui, QtWebKit
from dbexplorer.server.service import Service
import simplejson as json

class WebPage(QtWebKit.QWebPage):
    def javaScriptConsoleMessage(self, msg, line, source):
        print '%s line %d: %s' % (source, line, msg)
        pass
        
class NaService(QtCore.QObject):
    def __init__(self,tab,reverse):
        QtCore.QObject.__init__(self)        
        self.tab = tab
        self.isReverse = reverse
    
    @QtCore.Slot(str)
    def fieldSelected(self,fields_json):
        fields = json.loads(fields_json)        
        sc = []
        for i in range(0,len(fields)):            
            for f in fields[i]:
                (nomtable,nomcol)= f.split('__')
                tableItem = self.tab.findTableItemByNameOrAlias(nomtable)
                columnItem = self.tab.findColumnItem(tableItem.id,nomcol)
                sc.append((tableItem,columnItem,{'func':'','newname':'','group':'','order':None}))
                
        self.tab.selectedColumns = sc
        #self.tab.setDirty(True)
        self.tab.executeQuery()
                
    @QtCore.Slot()
    def reverse(self):
        tablesName,datasets = self.tab.getNaDataset(not self.isReverse)
        self.tab.naView.render(tablesName,datasets,not self.isReverse) 
        
    def readPP(self):
        return self.ppval
 
    def setPP(self,val):
        self.ppval = val
    
    def readReverse(self):
        return self.isReverse
        
    def setReverse(self,val):
        self.isReverse = val
            
    dataset = QtCore.Property(str, readPP, setPP)    
    isReverseVal = QtCore.Property(bool, readReverse, setReverse)

class NaIndividuService(QtCore.QObject):
    def __init__(self,tab,reverse):
        QtCore.QObject.__init__(self)        
        self.tab = tab
        self.isReverse = reverse
    
    def findTableId(self,tablename,tables):
        for t in tables:
            if tables[t]['tableName'] == tablename :
                return t
        return None
        
            
    @QtCore.Slot(str)
    def fieldSelected(self,fields_json):
        fields = json.loads(fields_json)
        #fields = [[u'ligne 5632', u'ligne 5635', u'ligne 5634']]
        self.tab.selectedRows=[]
        subdomain={}
        for f in fields[0]:
            (k,key_value)= f.split(" ")
            if k not in subdomain:
                subdomain[k]=[]
            subdomain[k].append(key_value)                 
            self.tab.selectedRows.append(key_value)
        
        
        (tables,joins,sc,filtre)  = self.tab.buildQuery()
        
        ands=['ET']
        for k in subdomain:            
            tablename,nomcol = k.split("__")
            tableId = self.findTableId(tablename,tables)
            domain = subdomain[k]
            ors = ['OU']
            for val in domain:                                    
                ors.append([tableId,nomcol,u'=',-1,val,{u'null':False,u'empty':False}])
                
            ands.append(ors)
            
        self.tab.add_and_filters = ands
        self.tab.executeQuery()
        
    @QtCore.Slot()
    def reverse(self):
        tablesName,datasets = self.tab.getNaIndividuDataset(not self.isReverse)
        self.tab.naIndividuView.render(tablesName,datasets,not self.isReverse)
        
        
    
    def readPP(self):
        return self.ppval
 
    def setPP(self,val):
        self.ppval = val
        
    def readReverse(self):
        return self.isReverse
        
    def setReverse(self,val):
        self.isReverse = val
        
    dataset = QtCore.Property(str, readPP, setPP)   
    isReverseVal = QtCore.Property(bool, readReverse, setReverse) 
        
class NaIndividuView(QtGui.QWidget):
    def __init__(self,tab):
        QtGui.QWidget.__init__(self)        
        self.layout  = QtGui.QGridLayout()
        self.setLayout(self.layout)
        self.tab = tab
        
    def render(self,tablesName,datasets,reverse) :            
        self.tablesName = tablesName
        self.datasets = datasets
        
        self.naService = NaIndividuService(self.tab,reverse)
        
        try:
            if self.webView :
                self.layout.removeWidget(self.webView)
        except:
            pass
                
        self.webView = QtWebKit.QWebView()
        self.layout.addWidget(self.webView,0,0)
        self.webView.loadFinished.connect(self.loadFinished)
        
        page = WebPage()
        page.mainFrame().addToJavaScriptWindowObject("naService", self.naService)
        
        self.webView.setPage(page)
        
        
        
        self.webView.load(QtCore.QUrl("./resources/naMultipleWithDiv.html"))

        
    def loadFinished(self):
        for i in range(0,len(self.tablesName)):
            self.naService.dataset = self.datasets[i]
            self.webView.page().mainFrame().evaluateJavaScript('drawChartFromPython("%d","%s")'%(i,self.tablesName[i]));
    

class NaView(QtGui.QWidget):
    def __init__(self,tab):
        QtGui.QWidget.__init__(self)        
        self.layout  = QtGui.QGridLayout()
        self.setLayout(self.layout)
        self.tab = tab
        
    def render(self,tablesName,datasets,reverse) :            
        self.tablesName = tablesName
        self.datasets = datasets
        
        self.naService = NaService(self.tab,reverse)
        
        try:
            if self.webView :
                self.layout.removeWidget(self.webView)
        except:
            pass
                
        self.webView = QtWebKit.QWebView()
        self.layout.addWidget(self.webView,0,0)
        
        page = WebPage()
        page.mainFrame().addToJavaScriptWindowObject("naService", self.naService)        
        self.webView.setPage(page)
        
        
        self.webView.loadFinished.connect(self.loadFinished)
        
        self.webView.load(QtCore.QUrl("./resources/naMultipleWithDiv.html"))

        
    def loadFinished(self):
        for i in range(0,len(self.tablesName)):
            self.naService.dataset = self.datasets[i]
            self.webView.page().mainFrame().evaluateJavaScript('drawChartFromPython("%d","%s")'%(i,self.tablesName[i]));
        
    
    
    