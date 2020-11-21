# -*- coding: utf-8 -*-
"""
.. module:: preference
   :synopsis: Module d'affichage et de configuration des préférences de l'application
.. codeauthor:: pireh, amérique du nord, laurent frobert
"""
from PySide import QtGui
from PySide import QtCore
import i18n
import os
import shutil

class PreferenceDialog(QtGui.QDialog):
    def __init__(self,mainWindow):
        QtGui.QDialog.__init__(self)
        self.mainWindow = mainWindow
        layout = QtGui.QGridLayout()
        self.setLayout(layout)
        
        self.setWindowTitle(_(u"Préférences"))
        
        labelLangue=QtGui.QLabel(_(u"Choix de la Langue"))
        self.langueZone = self.getLanguePanel()
        
        labelFont = QtGui.QLabel(_(u"Taille police : "))
        self.fontZone = QtGui.QLineEdit()
        self.fontZone.setText(str(self.readFontSizefromconfig()))
        
        labelConfig = QtGui.QLabel(_(u"Dossier de paramétrage"))
        self.configZone = self.getConfigPathPanel()      
        
        self.includeConfig = QtGui.QCheckBox(_(u"Inclure le fichier de base de données"))
                                             
        okButton = QtGui.QPushButton(_(u"Appliquer au prochain redémarage"))
        cancelButton = QtGui.QPushButton(_(u"Annuler"))
        
        okButton.clicked.connect(self.okbuttonclicked)
        cancelButton.clicked.connect(self.cancelbuttonclicked)
                
        layout.addWidget(labelLangue,0,0,1,2)
        layout.addWidget(self.langueZone,1,0,1,2)
        
        layout.addWidget(labelFont,2,0)
        layout.addWidget(self.fontZone,2,1)
        
        layout.addWidget(labelConfig,3,0,1,2)
        layout.addWidget(self.configZone,4,0,1,2)
        layout.addWidget(self.includeConfig,5,0,1,2)
        
        layout.addWidget(okButton,6,0,1,2)
        layout.addWidget(cancelButton,7,0,1,2)
    
    
    def readFontSizefromconfig(self):
        from dbexplorer.server import service as serviceServer
        try :        
            f = open(os.path.join(serviceServer.getpath(),'current_font_size'), 'r')                
            size = f.read()                                                            
            f.close()  
        except:
            size = 12
            
        
        return size
    
    def okbuttonclicked(self):
        
        if self.configZone.selectFilePath.text() != self.mainWindow.service.getConfigPath():
            print 'nouveau rep : ' ,self.configZone.selectFilePath.text()            
            try:
                f = open("./configpath",'w')
                f.write(self.configZone.selectFilePath.text())
                f.close()
                #copie de l'ancien fichier de conf vers le nouveau répertoire ?
                
                if self.includeConfig.isChecked() and not os.path.exists(os.path.join(self.configZone.selectFilePath.text(),'storage.sqlite')): # todo : if ne faut pas que le fichier de conf  existe déjà dans la destination
                    
                    os.makedirs(os.path.join(self.configZone.selectFilePath.text(),'backup'))
                    srcfile = os.path.join(self.mainWindow.service.getConfigPath(),'storage.sqlite')
                    dstdir = os.path.join(self.configZone.selectFilePath.text(),'storage.sqlite')
                    shutil.copy(srcfile, dstdir)
                    
                
            except:
                print 'error configpath'
            
        
        for i in range(len(self.langueZone.radios)):                       
            if self.langueZone.radios[i].isChecked():
                (codelangue,langue) = self.langueZone.langues[i]                
                i18n.saveLang(codelangue,self.mainWindow.service.getConfigPath())
                
        
        if str(self.readFontSizefromconfig()) != self.fontZone.text(): 
            self.saveFontSize(self.fontZone.text())
            from dbexplorer.client.main import applyStylesheet
            applyStylesheet(self.fontZone.text())
            self.mainWindow.textSizeHasChanged(int(self.fontZone.text()))
            
        self.close()
            
    def saveFontSize(self,size):
        try :        
            configpath = self.mainWindow.service.getConfigPath()
            f = open(os.path.join(configpath,'current_font_size'), 'w')
            f.write(size)                                                            
            f.close()  
        except:
            pass

    
    def cancelbuttonclicked(self):
        self.close()
            
    def getLanguePanel(self):
        langues = i18n.getAvailableLangue()
        w = QtGui.QWidget()
        w.radios=[]
        w.langues = langues
        
        layout = QtGui.QGridLayout()
        w.setLayout(layout)
        for (codelangue,langue) in langues:
            c = QtGui.QRadioButton(langue)
            if codelangue == i18n.currentLang :
                c.setChecked(True)
            w.radios.append(c)    
                
            layout.addWidget(c)
            
        
        return w
    
    def getConfigPathPanel(self):
        w = QtGui.QWidget()
        w.selectFilePath = QtGui.QLineEdit(self.mainWindow.service.getConfigPath())        
        openFileNameButton = QtGui.QPushButton(_(u"Choisir un répertoire"))                
        openFileNameButton.clicked.connect(self.openDir)
        
        layout = QtGui.QGridLayout()
        w.setLayout(layout)
        
        layout.addWidget(w.selectFilePath)
        layout.addWidget(openFileNameButton)
        
        return w
    
    def openDir(self):
        options = QtGui.QFileDialog.Options()   
        fileName = QtGui.QFileDialog.getExistingDirectory( dir=self.configZone.selectFilePath.text(), options=QtGui.QFileDialog.ShowDirsOnly)
        
        if fileName:
            self.configZone.selectFilePath.setText(fileName)
            
            
    
        
            