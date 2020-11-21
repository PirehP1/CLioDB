# -*- coding: utf-8 -*-
"""
.. module:: Service
   :synopsis: Module de service pour appeler les traitements du serveurs 
.. codeauthor:: pireh, amérique du nord, laurent frobert
"""
import sys
from PySide import QtGui, QtCore
import Queue
import threading
iconPrefix = './img/'
import os,logging

class Service(QtGui.QDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        
        self.setWindowTitle(_(u'Veuillez patienter'))
        self.setModal(True)
                
        
        self.label = QtGui.QLabel()
        
        
        movie = QtGui.QMovie (os.path.join(iconPrefix,'loading.gif'))
        self.m = QtGui.QLabel()
        self.m.setMovie(movie)     
        
        
        self.timer = QtCore.QBasicTimer()
        
 
        posit = QtGui.QGridLayout()
        
        
        posit.addWidget(self.m, 0, 0,QtCore.Qt.AlignCenter)   
        posit.addWidget(self.label, 1, 0,QtCore.Qt.AlignCenter)
        
        
        movie.start ()
        self.setLayout(posit)
                
        
        self.toServerQueue = Queue.Queue(0)
        self.fromServerQueue = Queue.Queue(0)
                
        Worker(self.toServerQueue,self.fromServerQueue).start() # start a worker
    
    def __del__(self):        
        self.toServerQueue.put(None)
        
    def waitForResponse(self):
        
        
        self.timer.start(100, self)  
        self.raise_()  
        if self.exec_():         
            return self.result()
        else:
            return None # cancelled by user
    
    
     
    
            
    def timerEvent(self, event):   
        
        try :
            item = self.fromServerQueue.get_nowait()            
            
            self.timer.stop()                                                                
            self.response = item
            self.accept()
                                    
        except Queue.Empty:
            pass
        
    def result(self):
        return self.response
    
    
    
    #list des method contenu dans server.service
    
    def getConfigPath(self):
        self.label.setText(_(u"Récupération fichier configuration"))
        self.toServerQueue.put(['getConfigPath'])
        return self.waitForResponse()
    
    def isDatasourceNameExists(self,datasourceName):
        self.label.setText(_(u"Vérification de l'unicité du nom de la source de données"))
        self.toServerQueue.put(['isDatasourceNameExists',datasourceName])
        return self.waitForResponse()
    
    def getStats(self,conn,selectClause):
        self.label.setText(_(u"Chargement des statistiques de la table"))
        self.toServerQueue.put(['getStats',conn,selectClause])
        return self.waitForResponse()
    
    def saveExploration(self,did,explorationId,name,jsonData):
        self.label.setText(_(u"Sauvegarde de l'exploration"))
        self.toServerQueue.put(['saveExploration',did,explorationId,name,jsonData])
        return self.waitForResponse()
    
    def getExplorationDocument(self,explorationId):
        self.label.setText(_(u"Chargement de l'exploration"))
        self.toServerQueue.put(['getExplorationDocument',explorationId])
        return self.waitForResponse()
    
    def getExplorationsNameByDsId(self,id):
        self.label.setText(_(u'Récupération des noms des explorations'))
        self.toServerQueue.put(['getExplorationsNameByDsId',id])
        return self.waitForResponse()
    
    def getDatasource(self,datasourceId):
        self.label.setText(_(u'Récupération des informations de la source de données'))
        self.toServerQueue.put(['getDatasource',datasourceId])
        return self.waitForResponse()
    
    #-----------
    def getFieldsName(self,datasourceId,tableName):
        self.label.setText(_(u'Récupération des noms des colonnes '))
        self.toServerQueue.put(['getFieldsName',datasourceId,tableName])
        return self.waitForResponse()
    
    def getTablesNameById(self,id):
        self.label.setText(_(u'Récupération des noms des tables '))
        self.toServerQueue.put(['getTablesNameById',id])
        return self.waitForResponse()
    
    def getTablesName(self,engine,username,password,host,port,database,query):
        self.label.setText(_(u'Récupération de la liste des tables'))
        self.toServerQueue.put(['getTablesName',engine,username,password,host,port,database,query])
        return self.waitForResponse()
    
    def newDatasource(self,datasourceInfo): 
        self.label.setText(_(u'Enregistrement de la nouvelle source de données'))
        self.toServerQueue.put(['newDatasource',datasourceInfo])
        return self.waitForResponse()
    
    
    def getDatasourcesNameList(self):
        self.label.setText(_(u'Récupération des noms des sources de données'))
        self.toServerQueue.put(['getDatasourcesNameList'])
        return self.waitForResponse()
    
    def getTableSchema(self,datasourceId,tableName):
        self.label.setText(_(u'Récupération du schéma de la base de données'))
        self.toServerQueue.put(['getTableSchema',datasourceId,tableName])
        return self.waitForResponse()
    
    def setTableSchema(self,did,tableName,cols):
        self.label.setText(_(u'Sauvegarde nouveaux types'))
        self.toServerQueue.put(['setTableSchema',did,tableName,cols])
        return self.waitForResponse()
    
    def getColumnDetails(self,dsId,tableName,columnName,typenatif,type) :
        self.label.setText(_(u'Récupération du détails de la colonne'))
        self.toServerQueue.put(['getColumnDetails',dsId,tableName,columnName,typenatif,type])
        return self.waitForResponse()
    
    def getDataframe(self,datasourceId,tables,joins,selectedColumns,filtre): 
        self.label.setText(_(u'Récupération des données'))
        self.toServerQueue.put(['getDataframe',datasourceId,tables,joins,selectedColumns,filtre])
        return self.waitForResponse()
    
    def getDataScatterPlot(self,datasourceId,tables,joins,selectedColumns,filtre): 
        self.label.setText(_(u'Récupération des données'))
        self.toServerQueue.put(['getDataScatterPlot',datasourceId,tables,joins,selectedColumns,filtre])
        return self.waitForResponse()
    
    def getBurt(self,datasourceId,tables,joins,selectedColumns,filtre): 
        self.label.setText(_(u'Création du diagramme de burt'))
        self.toServerQueue.put(['getBurt',datasourceId,tables,joins,selectedColumns,filtre])
        return self.waitForResponse()
    
    def executeQuery(self,datasourceId,tables,joins,selectedColumns,filtre,thelimit,theoffset):        
        #print "executeQuery",datasourceId,tables,joins,selectedColumns,filtre,thelimit,theoffset
        self.label.setText(_(u'Exécution de la requête'))
        self.toServerQueue.put(['executeQuery',datasourceId,tables,joins,selectedColumns,filtre,thelimit,theoffset])
        return self.waitForResponse()
    
    def createView(self,did,nomVue,sql):
        self.label.setText(_(u'Création de la vue'))
        self.toServerQueue.put(['createView',did,nomVue,sql])
        return self.waitForResponse()
    
    def getCsv(self,datasourceId,tables,joins,selectedColumns,filtre,filename):
        self.label.setText(_(u'Exportation en CSV'))
        self.toServerQueue.put(['getCsv',datasourceId,tables,joins,selectedColumns,filtre,filename])
        return self.waitForResponse()
    
    def removeDatasource(self,datasourceId):
        self.label.setText(_(u'Suppression de la source de données'))
        self.toServerQueue.put(['removeDatasource',datasourceId])
        return self.waitForResponse()
    
    def removeExploration(self,exploId):
        self.label.setText(_(u"Suppression de l'exploration"))
        self.toServerQueue.put(['removeExploration',exploId])
        return self.waitForResponse()
    
    def getNAJointure(self,did,tables,joins,sc,filtre,reverse):
        self.label.setText(_(u"Récupération des NA"))
        self.toServerQueue.put(['getNAJointure',did,tables,joins,sc,filtre,reverse])
        return self.waitForResponse()
    
    def getNAIndividuJointure(self,did,tables,joins,sc,filtre,reverse):
        self.label.setText(_(u"Récupération des NA"))
        self.toServerQueue.put(['getNAIndividuJointure',did,tables,joins,sc,filtre,reverse])
        return self.waitForResponse()
         
    def getNA(self,datasourceId,tableName,reverse=True):
        self.label.setText(_(u"Récupération des NA"))
        self.toServerQueue.put(['getNA',datasourceId,tableName,reverse])
        return self.waitForResponse()
    
    def getNonNA(self,datasourceId,tableName):
        self.label.setText(_(u"Récupération des non NA"))
        self.toServerQueue.put(['getNonNA',datasourceId,tableName])
        return self.waitForResponse()
    
    def getColumnDetailsFromQuery(self,datasourceId,tables,joins,sc,filtre,index):
        self.label.setText(_(u"Récupération des Stats"))
        self.toServerQueue.put(['getColumnDetailsFromQuery',datasourceId,tables,joins,sc,filtre,index])
        return self.waitForResponse()
    
    def executeCustomSQL(self,datasourceId,sql):
        self.label.setText(_(u'Exécution de la requête'))
        self.toServerQueue.put(['executeCustomSQL',datasourceId,sql])
        return self.waitForResponse()
    
    def exportCustomSQLToCsv(self,datasourceId,sql,fileName):
        self.label.setText(_(u'Exportation en cours'))
        self.toServerQueue.put(['exportCustomSQLToCsv',datasourceId,sql,fileName])
        return self.waitForResponse()
    
    def getSqliteList(self):
        self.label.setText(_(u'Récupération des sources de données SQLite'))
        self.toServerQueue.put(['getSqliteList'])
        return self.waitForResponse()
    
    def getNAIndividu(self,datasourceId,tables,joins,selectedColumns,filtre,reverse):
        self.label.setText(_(u'Récupération des NA pour les individus'))
        self.toServerQueue.put(['getNAIndividu',datasourceId,tables,joins,selectedColumns,filtre,reverse])
        return self.waitForResponse()
    
    def getSampleData(self,datasourceId,tableName,col):
        self.label.setText(_(u'Récupération des 10 premiers éléments'))
        self.toServerQueue.put(['getSampleData',datasourceId,tableName,col])
        return self.waitForResponse()
    
    def isNewTypeValid(self,datasourceId,tableName,colname,newtype):
        self.label.setText(_(u'Vérification du nouveau typage'))
        self.toServerQueue.put(['isNewTypeValid',datasourceId,tableName,colname,newtype])
        return self.waitForResponse()
    
    def computeDataFramePhi2(self,dataf):
        self.label.setText(_(u'Calcul Phi2'))
        self.toServerQueue.put(['computeDataFramePhi2',dataf])
        return self.waitForResponse()
    
    def scatterplot_matrix(self,datacopy, names, types,plt):
        self.label.setText(_(u'Construction Scatter Plot'))
        self.toServerQueue.put(['scatterplot_matrix',datacopy, names, types,plt])
        return self.waitForResponse()
    
    def heatmap(self,x, row_header, column_header, row_method,
            column_method, row_metric, column_metric,
            color_gradient, filename,pylab,mpl,matplotlib):
        self.label.setText(_(u'Construction Heatmap'))
        self.toServerQueue.put(['heatmap',x, row_header, column_header, row_method,column_method, row_metric, column_metric,color_gradient, filename,pylab,mpl,matplotlib])
        return self.waitForResponse()
    
import traceback,sys
class Worker(threading.Thread):

    def __init__(self, fromClientQueue,toClientQueue):
        self.fromClientQueue = fromClientQueue
        self.toClientQueue = toClientQueue
        from dbexplorer.server import service as serverservice
        self.service = serverservice.Service()
        
        threading.Thread.__init__(self)

    def run(self):
        while 1:
            serviceAsk = self.fromClientQueue.get()
            logging.debug("serviceAsk %s"%(serviceAsk,))
            
            if serviceAsk is None:                
                break # reached end of queue
                        
            try:
                result = getattr(self.service, serviceAsk.pop(0))(*serviceAsk)
                
                #logging.debug(u"Service result %s"%(result,))
                self.toClientQueue.put(result)
            except Exception as e:
                #print 'exception : ',e
                logging.error("Service return serviceAsk=%s"%(serviceAsk))
                logging.exception(e)                
                self.toClientQueue.put(e)
                            
    