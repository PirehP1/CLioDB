# -*- coding: utf-8 -*-
"""
.. module:: main
   :synopsis: Classe de la fenêtre principale de l'application
.. codeauthor:: pireh, amérique du nord, laurent frobert
"""

from PySide.QtCore import *
from PySide.QtGui import *
import logging
from dbexplorer.client.d3.typeGrapheDatasource import TranstypageView
LOG_LEVEL=logging.ERROR

dbexplorer_version='1.6.18'

modif=[]
modif.append(u"* 1.6.18 : ")
modif.append(u"- correction pour sqlAlchemy 0.9 (problème avec Function) ")

modif.append(u"* 1.6.17 : ")
modif.append(u"- petite correction sur les vues ")

modif.append(u"* 1.6.16 : ")
modif.append(u"- ajout des vues (pour les sous-requetes) ")
modif.append(u"- correction sur le detail colonne quand base postgresql ")

modif.append(u"* 1.6.15 : ")
modif.append(u"- ajout gestion base postgresql ")

modif.append(u"* 1.6.14 : ")
modif.append(u"- correction impact changement de taille de police ")
modif.append(u"- ajout du nombre de résultat dans le SQL manuel ")

modif.append(u"* 1.6.13 : ")
modif.append(u"- correction scatter plot quand toute les valeurs d'une colonne sont vides ")
modif.append(u"- ajout de wordwrap=False dans les tables de résultats ")

modif.append(u"* 1.6.12 : ")
modif.append(u"- application du changement de taille sur la vue relation ")
modif.append(u"- correction problème sous linux suse ")

modif.append(u"* 1.6.11 : ")
modif.append(u"- application du changement de taille sur la vue relation (non terminé)")
modif.append(u"- application du changement de taille dans les divers tableaux")

modif.append(u"* 1.6.10 : ")
modif.append(u"- correction generation de la requete sql (encore)")

modif.append(u"* 1.6.9 : ")
modif.append(u"- correction generation de la requete sql")

modif.append(u"* 1.6.8 : ")
modif.append(u"- application du changement de police sans relancer l'application")
modif.append(u"- modification du requetage du sous domaine pour le graphique hierarchique")

modif.append(u"* 1.6.7 : ")
modif.append(u"- ajout de l'impacte du changement de police a plusieurs éléments graphique")

modif.append(u"* 1.6.6 : ")
modif.append(u"- ajout de la préférence 'taille police'")
modif.append(u"- correction pb reindexation graphe hierarchique (cf fedora)")
modif.append(u"- export csv du tableau phi2")
modif.append(u"- correction des entiers transformés en flottant")
modif.append(u"- correction problèmes suppression filtres")

modif.append(u"* 1.6.5 : ")
modif.append(u"- correction pb calcul phi2")

modif.append(u"* 1.6.4 : ")
modif.append(u"- rajout du -- aux intersections")

modif.append(u"* 1.6.3 : ")
modif.append(u"- résolution problème nansum")

modif.append(u"* 1.6.2 : ")
modif.append(u"- croisement données mise à zéro aux intersections")

modif.append(u"* 1.6.1 : ")
modif.append(u"- correction problème croisement de données")

modif.append(u"* 1.6.0 : ")
modif.append(u"- ajout menu aide/manuel")
modif.append(u"- ménage dans le code")


modif.append(u"* 1.5.9 : ")
modif.append(u"- modification du nom du graphe")
modif.append(u"- changement de la valeur aux intersections dans le tableau qualitatif")


        
import sys,os


from dbexplorer.client.service import Service as ClientService
from dbexplorer.server import service
        

class MainWindow(QMainWindow):
    """
    Classe de la fenêtre principale de l'application
    """
    def __init__(self):
        super(MainWindow, self).__init__()       
        
        # répertoire de l'utilisateur ($HOME)
        self.userDocument=QDesktopServices.storageLocation(QDesktopServices.DocumentsLocation)
        
        #chemin du répertoire de configuration de l'application
        self.dbexplorerPath = service.getpath()
        
        if not os.path.exists(self.dbexplorerPath) :
            os.makedirs(self.dbexplorerPath)
            
        #activation du niveau de log    
        logging.basicConfig(filename=os.path.join(self.dbexplorerPath,'log.txt'),level=LOG_LEVEL)
        logging.error("Starting")
        logging.error("dbexplorer version %s"%(dbexplorer_version))
        
        #répertoire de backup                
        self.backupPath = os.path.join(self.dbexplorerPath,'backup')
        
        #verification de l'existance de fichier de backup
        self.checkBackupPath() 
        self.backupId=0
        self.setWindowTitle(_(u'clioDB'))
        
        #construction des menus
        self.initMenu()
        
        self.service =  ClientService(parent=self)
        
        #construction du treeview des sources de données
        self.datasourcesTree = self.getDsTreeView()
        
        self.explorationsTab = QTabWidget()
        self.explorationsTab.setTabsClosable(True)
        self.explorationsTab.setMovable(True)
        self.explorationsTab.tabCloseRequested.connect(self.closeTab)
        
        #separateur entre le treeview et l'explorationsTab
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.datasourcesTree)
        splitter.addWidget(self.explorationsTab)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([150,200])
        self.setCentralWidget(splitter)

        self.statusBar().showMessage(_(u"Ready"))
        
        self.resize(800, 600)
        
        #source de données courante
        self.currentDatasource = None #(id,name)
        
        #centrage de la fenêtre
        scr = QApplication.desktop().screenGeometry()
        self.move( scr.center() - self.rect().center() )
        
        
    
    def checkIfBackupExists(self):
        """Détermine l'existence ou non d'explorations non sauvegardées à la suite (éventuel :-) d'un plantage de l'application. 
        Si des explorations non sauvegardées sont présentes une fenêtre de demande de restauration s'affiche
        """
        logging.debug("checkIfBackupExists begin")
        
        #liste le contenu du répertoire de backup
        backupFiles = os.listdir(self.backupPath)
        if len(backupFiles)>0:
            #il y a des backup
            logging.debug("backup files exists")
            
            msgBox = QMessageBox()
            msgBox.setWindowTitle(_(u'Reprise sur erreur'))
            msgBox.setText(_(u"Des sauvegardes automatiques d'explorations sont présentes"));
            msgBox.setInformativeText(_(u"Voulez vous rétablir ces explorations"))
            msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel );
            msgBox.setDefaultButton(QMessageBox.Ok)
            
            #affichage de la fenêtre de demande de restauration
            ret = msgBox.exec_()
            
            if ret == QMessageBox.Ok:
                #l'utilisateur choisi de restaurer les explorations
                logging.debug("restore backup file")
                #determination de l'id de la datasource
                #les explorations backupés sont obligatoirement de la même source de données
                #étant donné que seul une source de données en même temps peut être ouverte 
                did = int(backupFiles[0].split('_')[1]) # on prend le premier 
                                
                item = self.datasourcesTree.model().getDatasourceItemById(did)
                index = self.datasourcesTree.model().getIndexOfDatasourceItem(item)
                
                #ouverture automatique de la source de données correspondant à l'exploration                
                item.openDataSource()
                
                self.datasourcesTree.reset()
                self.stopWait()                
                
                #ouverture 'visuelle' de la source de données                
                self.datasourcesTree.expand(index)
                                
                self.setCurrentDatasource(item.id,item.name)
                
                #ouverture de toutes les explo backupé
                for bf in backupFiles:
                    f = open(os.path.join(self.backupPath,bf), 'r')
                    jsonData = f.read()                                                            
                    f.close()                    
                    [backupid,did,exploid] = bf[:-7].split('_') #remove .backup extension file and split on _ char
                    backupid = int(backupid)
                    did = int(did)
                    exploid = int(exploid)
                    if exploid!=-1:
                        # open exploration from 
                        newTab = self.decodeExploration(jsonData)        
                        self.explorationsTab.addTab(newTab,newTab.exploName)
                        newTab.setDirty(True)
                        explorationItem = self.datasourcesTree.model().getExplorationItemForIds(did,exploid)                        
                        explorationItem.explorationTab = newTab
                        self.closeExplorationAction.setEnabled(True)
                        self.exportDatasourceAction.setEnabled(True)
                        self.printAction.setEnabled(True)
                        self.duplicateExplorationAction.setEnabled(True)   
                        self.exporterExplorationAction.setEnabled(True)   
                        self.supprimerExplorationAction.setEnabled(True)                  
                        #on efface l'ancien fichier de backup
                        os.remove(os.path.join(self.backupPath,bf))
                        
                    else:
                        #l'exploration backupé était une nouvelle exploration (id=-1)
                        newTab = self.decodeExploration(jsonData)            
                        self.explorationsTab.addTab(newTab,newTab.exploName)
                        newTab.setDirty(True)
                        self.datasourcesTree.newExploration(did,newTab)
                        self.closeExplorationAction.setEnabled(True)
                        self.exportDatasourceAction.setEnabled(True)
                        self.printAction.setEnabled(True)
                        self.duplicateExplorationAction.setEnabled(True)  
                        self.exporterExplorationAction.setEnabled(True)   
                        self.supprimerExplorationAction.setEnabled(True)                   
                        os.remove(os.path.join(self.backupPath,bf))
                        
                    
                    
                    #on resauvegarde les explo courantes (car dirty et le global backup id est different)
                    for i in range(0,self.explorationsTab.count()):
                        tab = self.explorationsTab.widget(i)
                        tab.automaticBackup()
            else:                               
                logging.debug("remove backup files") 
                for bf in backupFiles:
                    os.remove(os.path.join(self.backupPath,bf))
            
        
    def textSizeHasChanged(self,newfontsize):
        """Notification d'un changement de police de caractères. Appel à son tour textSizeHasChanged de toutes les explorations ouvertes.
     
        :param newfontsize: la nouvelle taille de police
        :type name: int.        
     
        """
        for i in range(0,self.explorationsTab.count()):
            tab = self.explorationsTab.widget(i)
            tab.textSizeHasChanged(newfontsize)
                        
    def checkBackupPath(self):
        if not os.path.exists(self.backupPath) :
            try :
                logging.info('make backup dir')
                os.makedirs(self.backupPath)                
            except Exception as error:
                logging.error('checkBackupPath')
                logging.exception(error)
                
    
    def wait(self,msg):
        
        progressBar_ = QProgressBar() 
        progressBar_.setMaximum(0)
        progressBar_.setMinimum(0)
        self.statusBar().addPermanentWidget(progressBar_)
        
        progressBar_.show()
        
        
        pass
    
    def stopWait(self):        
        pass
    
    def quitFromMenu(self):        
        if self.currentDatasource:
            if self.closeCurrentDatasource():                
                self.service.__del__()
                qApp.quit()
        else:
            self.service.__del__()
            qApp.quit()
                 
    def closeEvent(self,event):        
        if self.currentDatasource:
            if self.closeCurrentDatasource():
                self.service.__del__()
                qApp.quit()
            else:
                event.ignore()
        else:
            self.service.__del__()
            qApp.quit()        
            
    def initMenu(self):        
        datasourceMenu = QMenu(_(u"Fichier"), self)
        newDatasourceAction = datasourceMenu.addAction(_(u"Importer une base de données"))
        newDatasourceAction.setShortcut("Ctrl+o") 
                               
        self.exportDatasourceAction = datasourceMenu.addAction(_(u"Exporter les résultats"))
                
        self.printAction = datasourceMenu.addAction(_(u"Imprimer"))
        self.printAction.setEnabled(False)
        self.printAction.triggered.connect(self.printDatasource)
        
        self.newExplorationAction = datasourceMenu.addAction(_(u"Nouvelle exploration"))
        self.newExplorationAction.setShortcut("Ctrl+n") 
        self.newExplorationAction.setEnabled(False)
        
        self.duplicateExplorationAction = datasourceMenu.addAction(_(u"Dupliquer l'exploration"))
        self.duplicateExplorationAction.setShortcut("Ctrl+d")
        self.duplicateExplorationAction.triggered.connect(self.duplicateExploration)
        self.duplicateExplorationAction.setEnabled(False)
        
        self.saveExplorationAction = datasourceMenu.addAction(_(u"Enregistrer l'exploration"))
        self.saveExplorationAction.setShortcut("Ctrl+S")
        self.saveExplorationAction.setEnabled(False)
        
        self.closeExplorationAction = datasourceMenu.addAction(_(u"Fermer l'exploration"))
        self.closeExplorationAction.setShortcut("Ctrl+w")
        self.closeExplorationAction.setEnabled(False)
        
        self.importExplorationAction = datasourceMenu.addAction(_(u"Importer une exploration"))        
        self.importExplorationAction.triggered.connect(self.importDatasourceExploration)
        self.importExplorationAction.setEnabled(False)
        
        self.exporterExplorationAction = datasourceMenu.addAction(_(u"Exporter l'exploration"))        
        self.exporterExplorationAction.triggered.connect(self.exportDatasourceExploration)
        self.exporterExplorationAction.setEnabled(False)
        
        quitAction = datasourceMenu.addAction(_(u"Quitter"))
        quitAction.setShortcut("Ctrl+Q")
        
        self.exportDatasourceAction.triggered.connect(self.exportDatasource) #export data csv
        self.exportDatasourceAction.setEnabled(False)
        
        newDatasourceAction.triggered.connect(self.newDatasource)
        self.newExplorationAction.triggered.connect(self.newExploration)
        
        self.saveExplorationAction.triggered.connect(self.saveExplorationFromMenu)
        self.closeExplorationAction.triggered.connect(self.closeExplorationFromMenu)
        
        quitAction.triggered.connect(self.quitFromMenu)
        
        
        
        
        
        editionMenu = QMenu(_(u"Edition"), self)
        self.supprimerDatasourceAction = editionMenu.addAction(_(u"Supprimer la base de données courante"))
        self.supprimerDatasourceAction.triggered.connect(self.supprimerDatasource)
        self.supprimerDatasourceAction.setEnabled(False)
        
        self.supprimerExplorationAction = editionMenu.addAction(_(u"Supprimer l'exploration courante"))
        self.supprimerExplorationAction.triggered.connect(self.supprimerExploration)
        self.supprimerExplorationAction.setEnabled(False)                
        
        self.preferenceMenu = editionMenu.addAction(_(u"Préférences"))
        self.preferenceMenu.triggered.connect(self.preferenceAction)
        self.preferenceMenu.setEnabled(True)
        
        
        
        
        helpMenu = QMenu(_(u"Aide"), self)
        aboutAction = helpMenu.addAction(_(u"Manuel d'utilisation"))
        aboutAction.setShortcut("Ctrl+h")
        aboutAction.triggered.connect(self.openManuelDialog)
        
        
        aproposAction = helpMenu.addAction(_(u"A propos"))        
        aproposAction.triggered.connect(self.openAboutDialog)
        
        creditAction = helpMenu.addAction(_(u"Crédit"))
        
        self.menuBar().addMenu(datasourceMenu)
        self.menuBar().addMenu(editionMenu)
        
               
        self.menuBar().addMenu(helpMenu)
    
    def preferenceAction(self):
        from preference import PreferenceDialog            
        self.preferenceDialog = PreferenceDialog(self)                                
        self.preferenceDialog.setModal(True)
        self.preferenceDialog.show()
                        
            
    def supprimerDatasource(self):
        (did,dname) = self.currentDatasource
        item = self.datasourcesTree.model().getDatasourceItemById(did)
                
        reply = QMessageBox.question(self, item.name,_(u"Voulez vous vraiment supprimer cette source de données ?"),
                                                  QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            
        if reply == QMessageBox.Yes:
            #supprimer toutes les explo de cet datasource
            for index in reversed(range(self.explorationsTab.count())):
                explorationTab = self.explorationsTab.widget(index)
                itemExplo = self.datasourcesTree.model().getExplorationItemForTab(did,explorationTab)
                itemExplo.explorationTab.setDirty(False)
                self.closeExploration(itemExplo)  
                
            self.closeCurrentDatasource()
            response = item.removeDatasource()
            if response == 'ok':                
                self.datasourcesTree.model().removeDatasource(item.id)
        
    
    def supprimerExploration(self):
        explorationTab = self.explorationsTab.widget(self.explorationsTab.currentIndex())
        (did,dname) = self.currentDatasource
        item = self.datasourcesTree.model().getExplorationItemForTab(did,explorationTab)
        
        reply = QMessageBox.question(self, item.name,_(u"Voulez vous vraiment supprimer l'exploration courante ?"),
                                                  QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            
        if reply == QMessageBox.Yes:
            response = self.service.removeExploration(item.id)
            if response == 'ok':
                item.explorationTab.setDirty(False)
                self.closeExploration(item)  
                self.datasourcesTree.model().removeExploration(item)                        
                
                    
    
    def exportDatasourceExploration(self):
        explorationTab = self.explorationsTab.widget(self.explorationsTab.currentIndex())
        (did,dname) = self.currentDatasource
        explo = self.datasourcesTree.model().getExplorationItemForTab(did,explorationTab)
        self.exportExploration(explo)
        
    def importDatasourceExploration(self):        
        (did,dname) = self.currentDatasource
        self.importExploration(did)
        
    def duplicateExploration(self):
        explorationTab = self.explorationsTab.widget(self.explorationsTab.currentIndex())
        self.copyExploration(explorationTab)
    
        
    def exportDatasource(self):        
        explorationTab = self.explorationsTab.widget(self.explorationsTab.currentIndex())
        explorationTab.openSaveCsv()
    
    def printDatasource(self):
        explorationTab = self.explorationsTab.widget(self.explorationsTab.currentIndex())
        dialog = QPrintPreviewDialog()
        dialog.paintRequested.connect(self.handlePaintRequest)
        dialog.exec_()
    
    def handlePaintRequest(self, printer):
        explorationTab = self.explorationsTab.widget(self.explorationsTab.currentIndex())
        painter = QPainter(printer)
        explorationTab.view.render(painter)
        
        
    def closeTab(self,index):
        explorationTab = self.explorationsTab.widget(index)
        (did,dname) = self.currentDatasource
        explorationItem = self.datasourcesTree.getExplorationItemForTab(did, explorationTab)
        return self.closeExploration(explorationItem)            
            
    
    def closeExploration(self,explorationItem):                
        explorationTab = explorationItem.explorationTab
        index = self.explorationsTab.indexOf(explorationTab)
        if explorationTab.dirty:
            #ask for save or not 
            msgBox = QMessageBox()
            msgBox.setWindowTitle(explorationItem.name)
            msgBox.setText(_(u"L'exploration a été modifiée"))
            msgBox.setInformativeText(_(u"Voulez vous enregistrer vos modifications"))
            msgBox.setStandardButtons(QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel);
            msgBox.setDefaultButton(QMessageBox.Save)
            ret = msgBox.exec_()
            
            if ret == QMessageBox.Save:
                self.saveExploration(explorationTab)
                explorationTab.backupTimer.stop()
                explorationTab.removeBackupFile()
                explorationItem.explorationTab = None
                self.explorationsTab.removeTab(index)
                
                if self.explorationsTab.count() == 0:
                    self.closeExplorationAction.setEnabled(False)
                    self.exportDatasourceAction.setEnabled(False)
                    self.printAction.setEnabled(False)
                    self.duplicateExplorationAction.setEnabled(False)
                    self.saveExplorationAction.setEnabled(False)
                    self.exporterExplorationAction.setEnabled(False)
                    self.supprimerExplorationAction.setEnabled(False)
                return True
            elif ret == QMessageBox.Discard:
                #do not save
                
                explorationTab.backupTimer.stop()
                explorationTab.removeBackupFile()  
                
                explorationItem.explorationTab = None
                
                self.explorationsTab.removeTab(index)
                
                if self.explorationsTab.count() == 0:
                    self.closeExplorationAction.setEnabled(False)
                    self.exportDatasourceAction.setEnabled(False)
                    self.printAction.setEnabled(False)
                    self.duplicateExplorationAction.setEnabled(False)
                    self.saveExplorationAction.setEnabled(False)
                    self.exporterExplorationAction.setEnabled(False)
                    self.supprimerExplorationAction.setEnabled(False)
                return True
            elif ret == QMessageBox.Cancel:
                #do nothing
                return False
        else:
            explorationTab.backupTimer.stop()
            explorationTab.removeBackupFile()
            explorationItem.explorationTab = None
            self.explorationsTab.removeTab(index)  
            
            if self.explorationsTab.count() == 0:
                self.closeExplorationAction.setEnabled(False) 
                self.exportDatasourceAction.setEnabled(False)
                self.printAction.setEnabled(False) 
                self.duplicateExplorationAction.setEnabled(False)
                self.saveExplorationAction.setEnabled(False)
                self.exporterExplorationAction.setEnabled(False)
                self.supprimerExplorationAction.setEnabled(False)
            return True
        
       
        
        
        
        
    def closeCurrentDatasource(self):
        canClose = True        
        for tabindex in range(0,self.explorationsTab.count()):
            if not self.closeTab(0):
                canClose = False
                break
            
            
        if canClose:            
            self.datasourcesTree.closeDatasource(self.currentDatasource[0])
            self.currentDatasource = None
            self.importExplorationAction.setEnabled(False)
            self.newExplorationAction.setEnabled(False)
            self.supprimerDatasourceAction.setEnabled(False)
            return True
        else:
            return False
        
        
    def canOpenDatasource(self):                
        if self.currentDatasource :
            if self.closeCurrentDatasource():                    
                return True
            else:
                return False
        else:
            return True
    
    def setCurrentDatasource(self,id,name):        
        self.currentDatasource = (id,name)
        self.importExplorationAction.setEnabled(True)
        self.newExplorationAction.setEnabled(True)
        self.supprimerDatasourceAction.setEnabled(True)
        
    def getDsTreeView(self):        
        from dbexplorer.client.datasource_tree import TreeModel,DatasourceTreeView
        
        view = DatasourceTreeView(self.service,self)
                
        return view
    
    def clickOnItem(self, index):                
        item = index.internalPointer()
        from dbexplorer.client.datasource_tree import DatasourceItem
        
        if isinstance(item,DatasourceItem) : 
            self.datasourcesTree.collapseAll()
            #check if we have to save something
            self.datasourcesTree.expand(index)            
        else:
            if self.datasourcesTree.isExpanded(index):
                self.datasourcesTree.collapse(index)
            else:
                self.datasourcesTree.expand(index)     
    
    def openAboutDialog(self):
        QMessageBox.about ( self, _(u"A propos"), "<h1>DbExplorer version %s</h1>%s"%(dbexplorer_version,'<br/>'.join(modif)) )
    
    def openManuelDialog(self):
        from dbexplorer.client.manuel import ManuelView
        self.manuelView = ManuelView()
        self.manuelView.show()
        
                            
    def newDatasource(self):        
        from dbexplorer.client.datasource_wizard import NewDataSourceWizard
        
        wizard = NewDataSourceWizard(self.service,parent=self)
        result = wizard.exec_()
        
        if result == QDialog.Accepted:
            
            (datasourceInfo,insertIntoTable) = wizard.result()
            
            if insertIntoTable is None:
                (datasourceId,datasourceName) = self.service.newDatasource(datasourceInfo)                
                self.datasourcesTree.newDatasource(datasourceId,datasourceName)
            else:
                (datasourceName,tableName) = insertIntoTable
                 
                dsItem = self.datasourcesTree.model().getDatasourceItemByName(datasourceName)
                
                if self.currentDatasource is not None and self.currentDatasource[0] == dsItem.id:
                    self.datasourcesTree.model().newTable(dsItem,tableName)
                                
        else:
            #print 'user have canceled'
            pass    
    
    
    
    def newExploration(self):        
        # utilisation de la base de donnÃ©e en cours
        # demande de sauvegarde de l'explo en cours si nÃ©cessaire ?
        
        from dbexplorer.client import exploration
        if self.currentDatasource :
            (did,dname) = self.currentDatasource             
            exploName = _(u'nouvelle exploration de %(nom)s')%{'nom':dname}
            tab = exploration.Tab(self.service,did,self,exploName = exploName)            
            self.explorationsTab.addTab(tab,exploName)
            tab.setDirty(True)
            self.datasourcesTree.newExploration(did,tab)
            self.closeExplorationAction.setEnabled(True)
            self.exportDatasourceAction.setEnabled(True)
            self.printAction.setEnabled(True)
            self.duplicateExplorationAction.setEnabled(True)
            self.exporterExplorationAction.setEnabled(True)
            self.supprimerExplorationAction.setEnabled(True)
            
            self.explorationsTab.setCurrentIndex(self.explorationsTab.indexOf(tab))
        else:
            msgBox = QMessageBox()
            msgBox.setText(_(u"Vous devez d'abord ouvrir une source de données"))
            msgBox.setIcon(QMessageBox.Information)
            msgBox.exec_()
        
    def decodeExploration(self,jsonData): 
        
        
        (did,dname) = self.currentDatasource
        
        import simplejson as json
        obj = json.loads(jsonData)
         
        startLabelIndexFiltersWidget = obj['startLabelIndexFiltersWidget']
        exploName = obj['exploName']
        
            
        from dbexplorer.client.exploration import Tab
        
        
        newTab = Tab(self.service,did,self,startLabelIndexFiltersWidget=startLabelIndexFiltersWidget,exploName = exploName,backupid=self.backupId)       
        self.backupId += 1
        
                
        
        #init          
        newTab.view.countByTable = obj['countByTable']
        newTab.view.nextId = obj['nextId']
        
        # add table
        for t in obj['tables']:            
            pos = QPoint(t['posx'],t['posy'])  
            tableItem = newTab.view.loadTable(t['id'],t['tableName'],t['tableAlias'],pos)
            if 'tableTypes' in t:
                for col in tableItem.columnsItem:
                    try:
                        colName = col.column['name']
                        typecol = t['tableTypes'][colName][1]
                        
                        col.column['type'] = typecol 
                        col.setIconType()
                    except:
                        pass
            
            #tableTypes[col.column['name']]=(col.column['typenatif'],col.column['type'])
            
            
        scs = obj['sc']
        for sc in scs:
            tableId = sc['tableId']
            columnName = sc['column']
            func = sc['func']
            newName = sc['newname']
            group = sc['group']
            order = sc['order'] #tab of 2 element or ''
            if order:
                order = (order[0],order[1])
                
            tableItem = newTab.findTableItem(tableId)                        
            
            if not tableItem:
                print  'openExploration : table id not found :',tableId
                return
            
            #now find colunmItem            
            columnItem = newTab.findColumnItem(tableId,columnName)
            
            if not columnItem:
                print  'openExploration : column not found :',columnName
                return
            
            #now construct the 'other' attribute
            other={'func':func,'newname':newName,'group':group,'order':order}
            
            newTab.selectedColumns.append((tableItem,columnItem,other))
            columnItem.isInSelect = True
            columnItem.preventCheckStateChanged = True
            columnItem.check.setCheckState(Qt.CheckState.Checked)
            columnItem.preventCheckStateChanged = False
            
            
        # filtres
        for f in obj['filtres']:
            filterName = f['name']
            
            
            filterValue = newTab.decodeFilter(f['filter'])
            newTab.queryTools.whereList.model().addFilter(filterName,filterValue)
                
        
        
        #et les joins
        
        joins = obj['joins']
        from dbexplorer.client.exploration import JoinGroup
        
        for l in joins:
            joinGroup = JoinGroup(newTab.findTableItem(l.pop(0)),newTab.view)            
            while l:
                [joinType,tableId,startTableId,startColumnName,endTableId,endColumnName ]= [l.pop(0),l.pop(0),l.pop(0),l.pop(0),l.pop(0),l.pop(0)]
                
                tableItem = newTab.findTableItem(tableId)
                
                start = newTab.findColumnItem(startTableId, startColumnName)
                end = newTab.findColumnItem(endTableId, endColumnName)
                
                
                joinGroup.addToGroup(joinType,tableItem,start,end)
                
            newTab.view.joins.append(joinGroup)
            
            
                            
        newTab.executeQuery()
        return newTab
    
    def openExploration(self,explorationItem):
        jsonData = self.service.getExplorationDocument(explorationItem.id)
        newTab = self.decodeExploration(jsonData)        
        self.explorationsTab.addTab(newTab,newTab.exploName)
        newTab.setDirty(False)
        explorationItem.explorationTab = newTab
        self.closeExplorationAction.setEnabled(True)
        self.exportDatasourceAction.setEnabled(True)
        self.printAction.setEnabled(True)
        self.duplicateExplorationAction.setEnabled(True)
        self.exporterExplorationAction.setEnabled(True)
        self.supprimerExplorationAction.setEnabled(True)
        
        self.explorationsTab.setCurrentIndex(self.explorationsTab.indexOf(newTab))
    
    
    def transtypageDatasource(self,did):
        (error,tables) = self.service.getTablesNameById(did)        
        self.d = QDialog()        
        w = TranstypageView(self,did,self.service,tables)
        okButton = QPushButton(_(u"Validez"))
        cancelButton = QPushButton(_(u"Annulez"))
        l = QGridLayout()
        l.addWidget(w,0,0,1,2)
        l.addWidget(cancelButton,1,0)
        l.addWidget(okButton,1,1)
        
        okButton.clicked.connect(self.d.accept)
        cancelButton.clicked.connect(self.d.reject)
        
        self.d.setLayout(l)
        w.render()
        self.d.setModal(True)
        
        response = self.d.exec_()
        
        if response == QDialog.Accepted:            
            newtypes = w.result()
            
            for tableName in newtypes:
                self.service.setTableSchema(did,tableName,newtypes[tableName])
            
        self.d.destroy()
        self.d = None
        
        
    def importExploration(self,did):
        # open dialog to choose a file 
        # load data
        # do as a new exploration
        fileName, filtr = QFileDialog.getOpenFileName(self,_(u"Importation"),self.userDocument,_("DbExplorer Files (*.dbe);;All Files (*)"))
        
        if fileName:
            f = open(fileName, 'r')
            jsonData = f.read()                                                            
            f.close()                    
                        
            newTab = self.decodeExploration(jsonData)            
            self.explorationsTab.addTab(newTab,newTab.exploName)
            newTab.setDirty(True)
            self.datasourcesTree.newExploration(did,newTab)
            self.closeExplorationAction.setEnabled(True) 
            self.exportDatasourceAction.setEnabled(True)
            self.printAction.setEnabled(True)
            self.duplicateExplorationAction.setEnabled(True)
            self.exporterExplorationAction.setEnabled(True)
            self.supprimerExplorationAction.setEnabled(True)
            
        
    
    def exportExploration(self,explorationItem):
         
        fileName, filtr = QFileDialog.getSaveFileName(self,_("Exportation"),os.path.join(self.userDocument,'export.dbe'),_(u"DbExplorer Files (*.dbe);;All Files (*)"))
    
        if fileName:
            description, ok = QInputDialog.getText(self, _("Exporter une exploration"),_(u"Description de l'exploration:"),QLineEdit.Normal,explorationItem.name)
        
            if ok:
                jsonData = self.service.getExplorationDocument(explorationItem.id)
                import simplejson as json
                obj = json.loads(jsonData)                      
                obj['exportDescription'] = description
                newJsonData = json.dumps(obj,indent=4)
                f = open(fileName, 'w')
                f.write(newJsonData)
                f.flush()
                f.close()
            
    '''          
    def createViewAction(self,explorationItem):
        nomVue, ok = QInputDialog.getText(self, _("Créer une vue de l'exploration"),_(u"Nom de la vue:"),QLineEdit.Normal,explorationItem.name)
        
        if ok:
            print "createView ",nomVue
            errorMsg = self.service.createView(explorationItem.id,nomVue)
            if errorMsg is not None:
                msgBox = QMessageBox()
                msgBox.setText(_(u"une erreur s'est produite : %(erreur)s"%{'erreur':errorMsg}))
                msgBox.setIcon(QMessageBox.Information)
                msgBox.exec_()
            else:
                #todo : refresh table list
                pass
    '''    
    def copyExploration(self,explorationTab):
        jsonData = explorationTab.toJson()
        newTab = self.decodeExploration(jsonData)
        
        exploName = _("copie de %(nom)s")%{'nom':newTab.exploName}
        
        self.explorationsTab.addTab(newTab,exploName)
        newTab.setName(exploName)
        newTab.setDirty(True)
        
        (did,dname) = self.currentDatasource
        self.datasourcesTree.newExploration(did,newTab)
        
        
    def changeNameExploration(self,explorationItem):
        newName, ok = QInputDialog.getText(self, _("Nom de l'exploration"),_("Nouveau nom de l'exploration:"),QLineEdit.Normal,explorationItem.name)
        
        if ok:                             
            explorationItem.explorationTab.setDirty(True)   
            explorationItem.explorationTab.setName(newName)
            explorationItem.name = newName
            self.datasourcesTree.update()
              
    
    def saveExplorationFromMenu(self):
        explorationTab = self.explorationsTab.currentWidget()
        self.saveExploration(explorationTab)
        
    
    def closeExplorationFromMenu(self):        
        self.closeTab(self.explorationsTab.currentIndex())
            
    def saveExploration(self,explorationTab):
        if explorationTab.dirty:
            jsonData = explorationTab.toJson()
            (did,dname) = self.currentDatasource
            explorationItem = self.datasourcesTree.getExplorationItemForTab(did,explorationTab)
            id = self.service.saveExploration(did,explorationItem.id,explorationTab.exploName,jsonData)
            explorationTab.removeBackupFile()
            if explorationItem.id == -1:
                explorationItem.id = id 
            explorationTab.setDirty(False)
    
    def afterShow(self, ):    
        '''
        method called after the show method to check if backup exploration exists
        '''
            
        from dbexplorer.client.datasource_tree import TreeModel
        self.model = TreeModel(self.service)
        self.datasourcesTree.setModel(self.model)
        try:
            self.checkIfBackupExists()
        except Exception as error:
            logging.error("checkIfBackupExists error")
            logging.exception(error)
        
def readFontSizefromconfig():
    from dbexplorer.server import service as serviceServer
    try :        
        f = open(os.path.join(serviceServer.getpath(),'current_font_size'), 'r')                
        size = f.read()                                                            
        f.close()  
    except:
        size = 12
        
    
    return size
'''
class MyStyle(QGtkStyle):
    def __init__(self):
        QGtkStyle.__init__(self)
        self.checkBoxSize = 20
        
    def setCheckboxSize(self,size):
        self.checkBoxSize = int(size)
        
    def pixelMetric(self,  metric,  option , widget ):
        
        if metric == QStyle.PM_IndicatorHeight:
            return self.checkBoxSize
        if metric == QStyle.PM_IndicatorWidth:
            return self.checkBoxSize
        
        return QGtkStyle.pixelMetric(self,metric,option,widget)
    
    
mystyle = MyStyle()
'''        
def applyStylesheet(fontsize):        
    sizeh = int(fontsize) + 4
    
    #print sizeh  
     
    if sizeh>24:
        sizeh=24
    
    """
    qcheckbox='''
    QCheckBox::indicator {width: %(sizeh)spx;height: %(sizeh)spx;} /* ::indicator */
    QCheckBox {spacing: 1px;background-color:blue}
    
    '''%{'sizeh':sizeh}
    """
    #sizeh=10
    qcheckbox='''
    QCheckBox::indicator {width: %(sizeh)spx;height: %(sizeh)spx;} /* ::indicator */
    QCheckBox {spacing: 1px;padding:1px}    
    QCheckBox {width: 5px;} /* ::indicator */
    '''%{'sizeh':sizeh}  
    
    
    
        
    stylesheet = '''
    * { font-size: %(size)spx }
    QComboBox {height:%(size)spx;padding: 5px;}
    QLineEdit {height:%(size)spx}
    QPushButton { height: %(size)spx;padding: 5px;}
    QMenu::item {height:%(size)spx; padding: 5px; }
    QMenu::item:selected {background: rgba(120, 120, 120, 150);}
    %(qcheckbox)s
    ''' % {'size':fontsize,'qcheckbox':qcheckbox} #
    from PySide.QtGui import qApp
    #from PySide.QtGui import *
    qApp.setStyleSheet("")
    qApp.setStyleSheet(stylesheet)
    #mystyle.setCheckboxSize(sizeh)
    
             
       
def launch():
    
    
    app = QApplication(sys.argv)
    fontsize = readFontSizefromconfig()
    
    applyStylesheet(fontsize)
    #qApp.setStyle(mystyle)
    win = MainWindow()
    win.show()
    
    win.afterShow()
    
    sys.exit(app.exec_())
       
if __name__ == "__main__":
    launch()        

