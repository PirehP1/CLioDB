# -*- coding: utf-8 -*-
"""
.. module:: manuel
   :synopsis: Module d'affichage de l'aide
.. codeauthor:: pireh, amérique du nord, laurent frobert
"""
import sys
from PySide import QtCore, QtGui, QtWebKit

    
class ManuelView(QtGui.QDialog):
    def __init__(self):
        QtGui.QDialog.__init__(self)
        
        self.layout  = QtGui.QGridLayout()
        self.setLayout(self.layout)
        
        self.webView = QtWebKit.QWebView()
        self.webView.setContextMenuPolicy(QtCore.Qt.NoContextMenu)
        self.layout.addWidget(self.webView,0,0,1,2) #3,2
        
        
        #page = WebPage()                
        #self.webView.setPage(page)
        self.webView.load(QtCore.QUrl("./resources/manuel/index.html"))

        
        
   

