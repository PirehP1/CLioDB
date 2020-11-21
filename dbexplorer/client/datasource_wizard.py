# -*- coding: utf-8 -*-
"""
.. module:: datasource_wizard
   :synopsis: Module pour l'affichage d'un wizard d'ajout de nouvelles source de données
.. codeauthor:: pireh, amérique du nord, laurent frobert
"""
from PySide.QtCore import *
from PySide.QtGui import *

class NewDataSourceWizard(QWizard):
    CHOOSE_ENGINE_PAGE = 0
    MYSQL_ENGINE_PAGE = 1
    POSTGRESQL_ENGINE_PAGE = 2
    SQLITE_ENGINE_PAGE = 3    
    CSV_ENGINE_PAGE = 4
    PARSING_CSV_PAGE = 5
    CHOOSE_SQLITE_DESTINATION_PAGE = 6
    SHOW_TABLES = 7
    FINISH_PAGE = 8
    
    
    def __init__(self,service,parent=None):
        #service is the provider of data (tableslistname ...)
        super(NewDataSourceWizard, self).__init__(parent)
        self.service = service
        self.setModal(True)
        
        self.addPage(ChooseEnginePage())
        self.addPage(MysqlPage())
        self.addPage(PostgresqlPage())
        self.addPage(SqlitePage())
        self.addPage(CsvPage())
        self.addPage(ParseCsvPage())
        self.addPage(ChooseSQLiteDestinationPage())                
        self.addPage(ShowTablesPage())
        self.addPage(FinishPage())
        
        
        self.setWindowTitle(_(u"Nouvelle source de données"))
        self.setStartId(NewDataSourceWizard.CHOOSE_ENGINE_PAGE)
        self.tablesName=[]
        self.engine = None
        self.csvfilepath = None
        self.insertIntoTable = None
    
    def result(self):
        
        login = self.field('login')
        password  = self.field('password')
        host  = self.field('host')
        port  = self.field('port')
        database  = self.field('base')
        
        
        if not login:
            login = None
            
        if not password:
            password = None
            
        if not host :
            host = None
            
        if not port :
            port = None
        
        if not database :
            database = None
        
        
            
        return ((self.field('datasourceName'),
                self.engine,
                login,
                password,
                host,
                port,
                database,None),self.insertIntoTable) 
            
    def accept(self):                
        super(NewDataSourceWizard, self).accept()
        
                
            
class ChooseEnginePage(QWizardPage):
    def __init__(self, parent=None):
        super(ChooseEnginePage, self).__init__(parent)

        self.setTitle(_(u"Choix du moteur de base de données"))
        groupBox = QGroupBox(u"")
        
        self.mysqlDatasourceRadioButton = QRadioButton("Mysql")
        self.postgresqlDatasourceRadioButton = QRadioButton("PostgreSQL")
        self.sqliteDatasourceRadioButton = QRadioButton("Sqlite")
        self.csvDatasourceRadioButton = QRadioButton("Csv")
        
        
        groupBoxLayout = QVBoxLayout()
        groupBoxLayout.addWidget(self.mysqlDatasourceRadioButton)
        groupBoxLayout.addWidget(self.postgresqlDatasourceRadioButton)        
        groupBoxLayout.addWidget(self.sqliteDatasourceRadioButton)
        groupBoxLayout.addWidget(self.csvDatasourceRadioButton)
        groupBox.setLayout(groupBoxLayout)
        
        
        layout = QGridLayout()        
        layout.addWidget(groupBox, 0,0)
        self.setLayout(layout)   
        
        self.mysqlDatasourceRadioButton.clicked.connect(self.completeChanged)
        self.postgresqlDatasourceRadioButton.clicked.connect(self.completeChanged)        
        self.sqliteDatasourceRadioButton.clicked.connect(self.completeChanged)
        self.csvDatasourceRadioButton.clicked.connect(self.completeChanged)
        
    def isComplete(self, *args, **kwargs):
        return self.mysqlDatasourceRadioButton.isChecked() or self.postgresqlDatasourceRadioButton.isChecked() or self.sqliteDatasourceRadioButton.isChecked()  or self.csvDatasourceRadioButton.isChecked()          
    
    def currentId(self):
        return NewDataSourceWizard.CHOOSE_ENGINE_PAGE
    
    def nextId(self):                
        if self.mysqlDatasourceRadioButton.isChecked():
            return NewDataSourceWizard.MYSQL_ENGINE_PAGE
        elif self.postgresqlDatasourceRadioButton.isChecked():
            return NewDataSourceWizard.POSTGRESQL_ENGINE_PAGE
        elif self.sqliteDatasourceRadioButton.isChecked():
            return NewDataSourceWizard.SQLITE_ENGINE_PAGE
        elif self.csvDatasourceRadioButton.isChecked():
            return NewDataSourceWizard.CSV_ENGINE_PAGE
        else: # never reach normaly
            return NewDataSourceWizard.CHOOSE_ENGINE_PAGE
            
class MysqlPage(QWizardPage):
    def __init__(self, parent=None):
        super(MysqlPage, self).__init__(parent)

        self.setTitle(_(u"Accès à la base Mysql"))        
        
        loginLabel = QLabel(_(u"Identifiant :"))
        loginLineEdit = QLineEdit()
        loginLabel.setBuddy(loginLineEdit)

        passwordLabel = QLabel(_(u"Mot de passe :"))
        passwordLineEdit = QLineEdit()
        passwordLabel.setBuddy(passwordLineEdit)
        passwordLineEdit.setEchoMode(QLineEdit.Password)
        
        hostLabel = QLabel(_(u"Serveur :"))
        hostLineEdit = QLineEdit()
        hostLabel.setBuddy(hostLineEdit)
        
        portLabel = QLabel(_(u"Port :"))
        portLineEdit = QLineEdit()
        portLabel.setBuddy(portLineEdit)
        
        baseLabel = QLabel(_(u"Base de données :"))
        baseLineEdit = QLineEdit()
        baseLabel.setBuddy(baseLineEdit)                
         
        self.registerField('login*', loginLineEdit)
        self.registerField('password', passwordLineEdit)
        self.registerField('host*', hostLineEdit)
        self.registerField('port', portLineEdit)
        self.registerField('base*', baseLineEdit)
        
        layout = QGridLayout()
        layout.addWidget(loginLabel, 0, 0)
        layout.addWidget(loginLineEdit, 0, 1)
        
        layout.addWidget(passwordLabel, 1, 0)
        layout.addWidget(passwordLineEdit, 1, 1)
        
        layout.addWidget(hostLabel, 2, 0)
        layout.addWidget(hostLineEdit, 2, 1)
        
        layout.addWidget(portLabel, 3, 0)
        layout.addWidget(portLineEdit, 3, 1)
        
        layout.addWidget(baseLabel, 4, 0)
        layout.addWidget(baseLineEdit, 4, 1)
        
        
        self.setLayout(layout)
    
    def initializePage(self, *args, **kwargs):
        wiz = self.wizard()
                        
            
    def validatePage(self, *args, **kwargs):          
              
        (error,tablesNameList) = self.wizard().service.getTablesName('mysql',self.field('login'),
                                                                            self.field('password'),
                                                                            self.field('host'),
                                                                            self.field('port'),
                                                                            self.field('base'),
                                                                            None)
        
        if error:        
            reply = QMessageBox.critical(self,
                    _(u"Erreur"), _(u"Impossible de se connecter à la base de données\nVérifiez les paramêtres\n%(error)s")%({'error':error}))
            return False
        
        self.wizard().engine ="mysql"                
        self.wizard().tablesName = tablesNameList
        return True        
        
    def currentId(self):
        return NewDataSourceWizard.MYSQL_ENGINE_PAGE
    
    def nextId(self):                        
        return NewDataSourceWizard.SHOW_TABLES

class PostgresqlPage(QWizardPage):
    def __init__(self, parent=None):
        super(PostgresqlPage, self).__init__(parent)

        self.setTitle(_(u"Accès à la base PostgreSQL"))        
        
        loginLabel = QLabel(_(u"Identifiant :"))
        loginLineEdit = QLineEdit()
        loginLabel.setBuddy(loginLineEdit)

        passwordLabel = QLabel(_(u"Mot de passe :"))
        passwordLineEdit = QLineEdit()
        passwordLabel.setBuddy(passwordLineEdit)
        passwordLineEdit.setEchoMode(QLineEdit.Password)
        
        hostLabel = QLabel(_(u"Serveur :"))
        hostLineEdit = QLineEdit()
        hostLabel.setBuddy(hostLineEdit)
        
        portLabel = QLabel(_(u"Port :"))
        portLineEdit = QLineEdit()
        portLabel.setBuddy(portLineEdit)
        
        baseLabel = QLabel(_(u"Base de données :"))
        baseLineEdit = QLineEdit()
        baseLabel.setBuddy(baseLineEdit)                
         
        self.registerField('login2*', loginLineEdit)
        self.registerField('password2', passwordLineEdit)
        self.registerField('host2', hostLineEdit)
        self.registerField('port2', portLineEdit)
        self.registerField('base2*', baseLineEdit)
        
        layout = QGridLayout()
        layout.addWidget(loginLabel, 0, 0)
        layout.addWidget(loginLineEdit, 0, 1)
        
        layout.addWidget(passwordLabel, 1, 0)
        layout.addWidget(passwordLineEdit, 1, 1)
        
        layout.addWidget(hostLabel, 2, 0)
        layout.addWidget(hostLineEdit, 2, 1)
        
        layout.addWidget(portLabel, 3, 0)
        layout.addWidget(portLineEdit, 3, 1)
        
        layout.addWidget(baseLabel, 4, 0)
        layout.addWidget(baseLineEdit, 4, 1)
        
        
        self.setLayout(layout)
    
    def initializePage(self, *args, **kwargs):
        wiz = self.wizard()
                        
            
    def validatePage(self, *args, **kwargs):          
              
        (error,tablesNameList) = self.wizard().service.getTablesName('postgresql',self.field('login2'),
                                                                            self.field('password2'),
                                                                            self.field('host2'),
                                                                            self.field('port2'),
                                                                            self.field('base2'),
                                                                            None)
        
        if error:            
                            
            #reply = QMessageBox.critical(self,_(u"Erreur"), _(u"Impossible de se connecter à la base de données\nVérifiez les paramêtres\n%(error)s")%({'error':error}))
            reply = QMessageBox.critical(self,_(u"Erreur"), str(error))
            return False
        
        self.wizard().engine ="postgresql"
        self.wizard().setField("login",self.field('login2'))
        self.wizard().setField("password",self.field('password2'))
        self.wizard().setField("host",self.field('host2'))
        self.wizard().setField("port",self.field('port2'))
        self.wizard().setField("base",self.field('base2'))
        self.wizard().tablesName = tablesNameList
        return True        
        
    def currentId(self):
        return NewDataSourceWizard.POSTGRESQL_ENGINE_PAGE
    
    def nextId(self):                        
        return NewDataSourceWizard.SHOW_TABLES
        
class SqlitePage(QWizardPage):
    def __init__(self, parent=None):
        super(SqlitePage, self).__init__(parent)

        self.setTitle(_(u"Accès à la base Sqlite"))
        
        selectFileLabel = QLabel(_(u"chemin du fichier :"))
        self.selectFilePath = QLineEdit()
        selectFileLabel.setBuddy(self.selectFilePath)
        openFileNameButton = QPushButton(_(u"Choisir un fichier"))
        
        
        openFileNameButton.clicked.connect(self.setOpenFileName)
        self.registerField('filePath*',self.selectFilePath)
        
        layout = QGridLayout()
        layout.addWidget(selectFileLabel, 0, 0)
        layout.addWidget(self.selectFilePath, 0, 1)
        
        layout.addWidget(openFileNameButton, 1, 0)
        
        self.setLayout(layout)
    
    def setOpenFileName(self):    
        options = QFileDialog.Options()        
        fileName, filtr = QFileDialog.getOpenFileName(self,
                _(u"Sélectionner un fichier sqlite3"),
                self.selectFilePath.text(),
                _(u"Tous les fichiers (*)"), options=options)
        if fileName:
            self.selectFilePath.setText(fileName)

    def initializePage(self, *args, **kwargs):
        return QWizardPage.initializePage(self, *args, **kwargs)
    
    
    def validatePage(self, *args, **kwargs):        
        (error,tablesNameList) = self.wizard().service.getTablesName('sqlite',None,None,None,None,self.field('filePath'),None)
        
        if error:        
            QMessageBox.critical(self,
                    _(u"Erreur"), _(u"Impossible de se connecter à la base de données\nVérifiez les paramêtres\n%(error)s")%{'error':error})
            return False
        
        self.wizard().engine ="sqlite"   
        self.setField('base',self.field('filePath'))
        self.wizard().tablesName = tablesNameList
        
        return True
        
    def currentId(self):
        return NewDataSourceWizard.SQLITE_ENGINE_PAGE
    
    def nextId(self):                        
        return NewDataSourceWizard.SHOW_TABLES
    
class ShowTablesPage(QWizardPage):
    def __init__(self, parent=None):
        super(ShowTablesPage, self).__init__(parent)

        self.setTitle(_(u"Connexion réussie"))

        tablesListLabel = QLabel(_(u"voici les tables disponibles"))
        self.tablesList = QListWidget()
        
        connectionLabel = QLabel(_(u"<b>entrez un nom pour cette source de données :</b>"))        
        connectionLineEdit = QLineEdit()
        connectionLabel.setBuddy(connectionLineEdit)
        
        self.registerField('datasourceName*', connectionLineEdit)
        
        layout = QGridLayout()        
        layout.addWidget(tablesListLabel, 0,0)
        layout.addWidget(self.tablesList, 1,0)
        layout.addWidget(connectionLabel, 3,0)
        layout.addWidget(connectionLineEdit, 4,0)
        
        self.setLayout(layout)  
        
    def initializePage(self, *args, **kwargs):        
        self.tablesList.clear()
        for table in self.wizard().tablesName: 
            qtItem = QListWidgetItem(self.tablesList)
            qtItem.setText(table)
        
        
        return QWizardPage.initializePage(self, *args, **kwargs)    
    
    def currentId(self):
        return NewDataSourceWizard.SHOW_TABLES

    def isFinalPage(self, *args, **kwargs):
        return True
        
    def validatePage(self, *args, **kwargs):
        #check if datasourcename not already exists   
        datasourceName = self.field('datasourceName')
                     
        
        if self.wizard().service.isDatasourceNameExists(datasourceName):
            QMessageBox.critical(self,_(u"Erreur"), _(u"Nom de source de données déjé existant"))
            return False
        
        return True

class CsvPage(QWizardPage):
    def __init__(self, parent=None):
        super(CsvPage, self).__init__(parent)

        self.setTitle(_(u"Accès au fichier CSV"))
        
        selectFileLabel = QLabel(_(u"chemin du fichier :"))
        self.selectFilePath = QLineEdit()
        selectFileLabel.setBuddy(self.selectFilePath)
        openFileNameButton = QPushButton(_(u"Choisir un fichier"))
        
        
        openFileNameButton.clicked.connect(self.setOpenFileName)
        self.registerField('csvfilePath*',self.selectFilePath)
        
        layout = QGridLayout()
        layout.addWidget(selectFileLabel, 0, 0)
        layout.addWidget(self.selectFilePath, 0, 1)
        
        layout.addWidget(openFileNameButton, 1, 0)
        
        self.setLayout(layout)
    
    def setOpenFileName(self):    
        options = QFileDialog.Options()        
        fileName, filtr = QFileDialog.getOpenFileName(self,
                _(u"Sélectionner un fichier csv"),
                self.selectFilePath.text(),
                _(u"fichier csv (*.csv);;Tous les fichiers (*)"), options=options)
        if fileName:
            self.selectFilePath.setText(fileName)

    def initializePage(self, *args, **kwargs):
        return QWizardPage.initializePage(self, *args, **kwargs)
    
    
    def validatePage(self, *args, **kwargs):
        import os
        if not os.path.exists(self.selectFilePath.text()):                 
            QMessageBox.critical(self,_(u"Erreur"), _(u"Impossible d'acceder au fichier"))
            return False  
        
        self.wizard().csvfilepath = self.selectFilePath.text()
        return True    
    
    def currentId(self):
        return NewDataSourceWizard.CSV_ENGINE_PAGE
    
    def nextId(self):                        
        return NewDataSourceWizard.PARSING_CSV_PAGE


#from ucsv import unicodecsv as csv
import dbexplorer.client.ucsv as csv
class CsvDialect(csv.Dialect):    
    # Séparateur de champ
    delimiter = ";"    
    
class CsvModel(QAbstractTableModel):
    def __init__(self,datas):
        QAbstractTableModel.__init__(self)
        self.datas = datas        
        
    def rowCount(self, parent=QModelIndex()):                
        return len(self.datas)
        
    def columnCount(self, parent=QModelIndex()):        
        return len(self.datas[0])
    
    def data(self,index, role=Qt.DisplayRole):
        row = index.row()
        column = index.column()
        if role == Qt.DisplayRole:            
            return self.datas[row][column]
        elif role == Qt.EditRole and row == 0:
            return self.datas[row][column]
        
        return None

    def getDatas(self):
        return self.datas
    
    def setData(self, index, value, role=Qt.EditRole):
        row = index.row()
        column = index.column()
        if row == 0:
            self.datas[row][column] = value
            return True
        
        
        return False
    
    def flags(self, index):
        row = index.row()
        column = index.column()
        if row == 0:
            return Qt.ItemIsEditable | Qt.ItemIsEnabled
        else:
            return QAbstractTableModel.flags(self,index)
        
    
class ParseCsvPage(QWizardPage):
    def __init__(self, parent=None):
        super(ParseCsvPage, self).__init__(parent)

        self.setTitle(_(u"Analyse du fichier CSV"))                
        
        layout = QGridLayout()
        self.tableNameLabel = QLabel(_(u'Nom pour cette table'))                
        self.tableName = QLineEdit(_(u'matable'))
                
        self.errorZone = QPlainTextEdit()
           
        
        
        m = self.errorZone.fontMetrics()
        rowHeight = m.lineSpacing()
        self.errorZone.setFixedHeight  (3 * rowHeight)
                
        self.firstLineIsColumnsNameCheckbox = QCheckBox(_(u'nom de colonne\ndans la première ligne'))
        self.fieldSeparatorLabel = QLabel(_(u'séparateur de champs')) 
                 
        self.fieldSeparator = QLineEdit(',')
                
        self.resultset = QTableView()
        
        
        ypos = 0
        layout.addWidget(self.tableNameLabel,ypos,0,1,1)        
        layout.addWidget(self.tableName,ypos,1,1,3)
        ypos+=1
        layout.addWidget(self.firstLineIsColumnsNameCheckbox,ypos,0,1,1)        
        layout.addWidget(self.fieldSeparatorLabel,ypos,1,1,1)        
        layout.addWidget(self.fieldSeparator,ypos,2,1,1)
        ypos+=1
                       
        layout.addWidget(self.errorZone,ypos,0,1,4)
        ypos+=1
        
        layout.addWidget(self.resultset,ypos,0,1,4)
    
        self.setLayout(layout)            
        
        self.firstLineIsColumnsNameCheckbox.clicked.connect(self.parse)        
        self.fieldSeparator.setMaxLength(1)
        self.fieldSeparator.setFixedWidth(20)
        self.fieldSeparator.textChanged.connect(self.parse)
        
        
        
        self.dialect = csv.Dialect
        self.model = None
        self.errors=[]
        
    def initializePage(self, *args, **kwargs):
        
        self.firstLineIsColumnsNameCheckbox.setChecked(False)        
        self.fieldSeparator.setText(",")
        
        self.parse()
        return QWizardPage.initializePage(self, *args, **kwargs)
    
            
    def parse(self):
        try:
            csvfilepath = self.wizard().csvfilepath        
        
            
            import dbexplorer.client.ucsv as csv
            self.dialect.delimiter = str(self.fieldSeparator.text())
            
            
                    
            reader = csv.reader(open(csvfilepath, "rb"),delimiter=str(self.fieldSeparator.text()))            
            datas = []
            
            self.errors=[]
            line = -1
            for fields in reader:
                line +=1
                f=[]
                for field in fields:
                    try:
                        f.append(unicode(field))
                    except:
                        f.append(field)   
                    
                if line>0 and len(f) != len(datas[0]) :                    
                    self.errors.append(_(u'ligne %(lineNumber)d : nombre de colonnes de correspondent pas ')%{'lineNumber':(line+1)})
                                  
                datas.append(f)
            
            if not self.firstLineIsColumnsNameCheckbox.isChecked():
                headers = ['col%d'%(i,) for i in range(1,len(datas[0])+1)] 
                datas.insert(0, headers)    
            
            if len(self.errors) == 0:
                self.errorZone.setPlainText(_(u'Aucune erreur'))
            else:    
                self.errorZone.setPlainText('\n'.join(self.errors))
                
            self.model = CsvModel(datas)    
            self.resultset.setModel(self.model)
        except:
            import traceback
            import sys
            traceback.print_exc(file=sys.stdout)
            self.model = None            
            self.errorZone.setPlainText(_(u"Erreur d'analyse"))
            self.resultset.setModel(self.model)        
            
        
    
    def validatePage(self, *args, **kwargs):
        if len(self.errors)>0:
            return False  
        
        
        if self.model:            
            self.wizard().csvdata = self.model.getDatas()  
            self.wizard().tablesName = [self.tableName.text()]
                
            return True
        else:
            return False 
        
        return False
    
    def currentId(self):
        return NewDataSourceWizard.PARSING_CSV_PAGE
    
    def nextId(self):                        
        return NewDataSourceWizard.CHOOSE_SQLITE_DESTINATION_PAGE

class ChooseSQLiteDestinationPage(QWizardPage):
    def __init__(self, parent=None):
        super(ChooseSQLiteDestinationPage, self).__init__(parent)

        self.setTitle(_(u"Enregistrer vers un fichier SQLite"))
        
        selectFileLabel = QLabel(_(u"chemin du fichier :"))
        self.selectFilePath = QLineEdit('')
                        
        
        self.selectFilePath.setEnabled(False)
        selectFileLabel.setBuddy(self.selectFilePath)
        openFileNameButton = QPushButton(_(u"Choisir un fichier"))
        #self.wizard().insertIntoTable = False
        
        openFileNameButton.clicked.connect(self.setOpenFileName)        
        
        oubien = QLabel(_(u'Ou bien une base sqlite déjà existante :'))
        self.dsList = QComboBox()
        
        
        layout = QGridLayout()
        layout.addWidget(selectFileLabel, 0, 0)
        layout.addWidget(self.selectFilePath, 0, 1)        
        layout.addWidget(openFileNameButton, 1, 0,1,2)
        layout.addWidget(oubien,2,0,1,2)
        layout.addWidget(self.dsList,3,0,1,2)
        self.setLayout(layout)
        
        
    def setOpenFileName(self):    
        options = QFileDialog.Options()          
              
        fileName, filtr = QFileDialog.getSaveFileName(self,
                _(u"Sélectionner un fichier sqlite3"),
                self.selectFilePath.text(),
                _(u"Tous les fichiers (*)"), options=options)
        if fileName:
            self.selectFilePath.setText(fileName)

    def initializePage(self, *args, **kwargs):
        self.wizard().insertIntoTable = None
        self.dsList.clear()
        result = self.wizard().service.getSqliteList()        
        (self.filenames,self.sqliteList) = result
        
        self.filenames.insert(0,'')
        self.sqliteList.insert(0,'')
        self.dsList.addItems(self.sqliteList)
        
        
        return QWizardPage.initializePage(self, *args, **kwargs)
    
    
    def validatePage(self, *args, **kwargs):
        if len(self.selectFilePath.text()) == 0  and self.dsList.currentIndex() == 0:
            return False
        
        try :
            #creation table
            import sqlite3
            
            filename = None
            if len(self.selectFilePath.text())>0:
                filename = self.selectFilePath.text()                
            else:
                filename = self.filenames[self.dsList.currentIndex()]
                self.wizard().insertIntoTable = (self.sqliteList[self.dsList.currentIndex()],self.wizard().tablesName[0])
            
            conn = sqlite3.connect( filename )
            conn.text_factory = str  #bugger 8-bit bytestrings
            
            data = self.wizard().csvdata
            
            fieldsCreation = []
            fields = []
            emptyField = []
            for f in data[0]:
                fieldsCreation.append(u'%s VARCHAR'%(f,))
                fields.append(u'%s'%(f,))
                emptyField.append(u'?')
                
            tableName = self.wizard().tablesName[0]
            sql = u'CREATE TABLE IF NOT EXISTS %s (%s)'%(tableName,u','.join(fieldsCreation))            
            conn.execute(sql)
            
            
            fieldsInsert = ','.join(fields)
            emptyFieldInsert = ','.join(emptyField)
            for line in range(len(data)):
                if line == 0: # header
                    continue
                sql2='INSERT OR IGNORE INTO %s (%s) VALUES (%s)'%(tableName,fieldsInsert,emptyFieldInsert)
                conn.execute(sql2, tuple(data[line]))
            
            conn.commit()   
            conn.close()
            
            
            
            
            self.wizard().engine ="sqlite"   
            self.setField('base',self.selectFilePath.text())
            
            
            
            
            
            return True
        except Exception as e:
            import traceback
            import sys
            traceback.print_exc(file=sys.stdout)
            msgBox = QMessageBox()
            msgBox.setText(_(u"erreur lors de l'import du fichier CSV  %(msg)s:")%{'msg':str(e)})
            msgBox.setIcon(QMessageBox.Critical)
            msgBox.exec_()  
            return False
    
    def currentId(self):
        return NewDataSourceWizard.CHOOSE_SQLITE_DESTINATION_PAGE
    
    
    def nextId(self, *args, **kwargs):
        if self.wizard().insertIntoTable is not None:
            return NewDataSourceWizard.FINISH_PAGE
        else:
            return NewDataSourceWizard.SHOW_TABLES  

class FinishPage(QWizardPage):
    def __init__(self, parent=None):
        super(FinishPage, self).__init__(parent)

        self.setTitle(_(u"Enregistrement terminé"))
        
        
        
        
        
    def validatePage(self, *args, **kwargs):
        return True
    
    def isFinalPage(self, *args, **kwargs): 
        return True        
        
    def currentId(self):
        return NewDataSourceWizard.FINISH_PAGE
    
          

                  
