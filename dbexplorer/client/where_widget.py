# -*- coding: utf-8 -*-

"""
.. module:: where_widget
   :synopsis: Module de création/modification des filtres de requêtes  
.. codeauthor:: pireh, amérique du nord, laurent frobert
"""
from PySide.QtCore import *
from PySide.QtGui import *
from xml.sax.saxutils import escape
from decimal import Decimal
import os

iconPrefix = './img/'



def getTableName(tableItem):
        if tableItem.alias:
            return tableItem.alias
        else:
            return tableItem.name


class FieldsModel(QAbstractListModel):
    def __init__(self,tableItemList):
        QAbstractListModel.__init__(self)
        self.fieldsList = []
        
        # construct the field list        
        for tableItem in tableItemList:
            for columnItem in tableItem.columnsItem:
                self.fieldsList.append(columnItem)
        
        
    def rowCount(self,parent= QModelIndex()):
        return len(self.fieldsList)
     
    def data(self, index, role = Qt.DisplayRole):        
        if role == Qt.DisplayRole:
            columnItem = self.fieldsList[index.row()]
            tableItem = columnItem.parentItem()
            t1 = getTableName(tableItem) 
            return  "%s.%s"%(t1,columnItem.column['name'])
        elif role == Qt.EditRole :            
            return self.fieldsList[index.row()]         
        
        return None
    
    def findIndex(self,value):
        try:
            index = self.fieldsList.index(value)
            if index!=-1:
                return self.createIndex(index,0,None)
            else:
                return QModelIndex()
        except ValueError:
            return QModelIndex()



class AbstractOperatorModel(QAbstractListModel):
    def __init__(self,valuesList):
        QAbstractListModel.__init__(self)
        self.valuesList = valuesList
                
    def rowCount(self,parent= QModelIndex()):
        return len(self.valuesList)
     
    def data(self, index, role = Qt.DisplayRole):        
        if role == Qt.DisplayRole:
            (value,label) = self.valuesList[index.row()]                        
            return  label
        elif role == Qt.EditRole :                                            
            return self.valuesList[index.row()]
        
        return None
    
    def findIndex(self,value):
        try :
            index = [y[0] for y in self.valuesList].index(value)
            if index!=-1:
                return self.createIndex(index,0,None)
            else:
                return QModelIndex()
        except ValueError:
            return QModelIndex()
        
class YesNoModel(AbstractOperatorModel): # numeric pour DEC ou INT type
    def __init__(self):
        valuesList = [(True,_(u'oui')),
                      (False,_(u'non')),
                      (True,_(u'vrai')),
                      (False,_(u'faux'))
                           ]
        AbstractOperatorModel.__init__(self,valuesList)


class NumericOperatorModel(AbstractOperatorModel): # numeric pour DEC ou INT type
    def __init__(self):
        valuesList = [('>',_(u'supérieur à')),
                           ('=',_(u'égal à')),
                           ('<',_(u'inférieur à ')),
                           ('>=',_(u'supérieur ou égal à')),
                           ('<=',_(u'inférieur ou égal à')),
                           ('!=',_(u'différent de'))]
        AbstractOperatorModel.__init__(self,valuesList)

            
class TemporalOperatorModel(AbstractOperatorModel):
    def __init__(self):
        valuesList = [('>',_(u'après')),
                      ('<',_(u'avant')),                      
                      ('=',_(u'égal à')),
                      ('!=',_(u'différent de'))
                      ]
        AbstractOperatorModel.__init__(self,valuesList)

class BooleanOperatorModel(AbstractOperatorModel):
    def __init__(self):
        valuesList = [('=',_(u'est')),
                      ('!=',_(u"n'est pas "))                      
                      ]
        AbstractOperatorModel.__init__(self,valuesList)

        
class StringOperatorModel(AbstractOperatorModel):
    def __init__(self):
        valuesList = [('startswith',_(u'commence par')),
                      ('contains',_(u'contient')),
                      ('!=',_(u'différent de')),
                      ('=',_(u'égal à')),
                      ('endswith',_(u'termine par'))                      
                      ]
        AbstractOperatorModel.__init__(self,valuesList)

class AllOperatorModel(AbstractOperatorModel):
    def __init__(self):
        valuesList = [('startswith',_(u'commence par')),
                      ('endswith',_(u'termine par')),
                      ('contains',_(u'contient')),                      
                      ('>',_(u'supérieur à')),
                       ('=',_(u'égal à')),
                       ('<',_(u'inférieur à ')),
                       ('>=',_(u'supérieur ou égal à')),
                       ('<=',_(u'inférieur ou égal à')),
                       ('!=',_(u'différent de'))
                      ]
        AbstractOperatorModel.__init__(self,valuesList)
        
        
class FieldFilter(QSortFilterProxyModel):
    def __init__(self,typesToKeep):
        QSortFilterProxyModel.__init__(self)
        self.typesToKeep = typesToKeep
        
    def filterAcceptsRow(self,source_row, source_parent):
        
        columnItem = self.sourceModel().createIndex(source_row,0,None).data(Qt.EditRole)        
        if columnItem and columnItem.column['type'] in self.typesToKeep:
            return True
        else: 
            return False
        
    def findIndex(self,searchvalue):        
        index = self.sourceModel().findIndex(searchvalue)
        return self.mapFromSource(index)
            
class AbstractEditor(QWidget):
    def __init__(self,fieldsModel,parent=None):
        QWidget.__init__(self,parent=parent)        
        layout = QGridLayout()
        self.setLayout(layout)
        
        self.operators = QListView()                
        
        self.freeText = QLineEdit()
        
        self.caseCheckbox = QCheckBox(_(u'insensible à la casse'))
        self.caseCheckbox.hide()
        
        self.nullCheckbox = QCheckBox(_(u'non renseigné'))
        self.emptyCheckbox = QCheckBox(_(u'vide'))
        


        self.otherFields = QListView()        
        
        layout.addWidget(self.operators,0,0,4,1)
        layout.addWidget(self.freeText,0,1,1,2)
        layout.addWidget(self.caseCheckbox,1,1)
        layout.addWidget(self.nullCheckbox,2,1)
        layout.addWidget(self.emptyCheckbox,2,2)
        layout.addWidget(self.otherFields,3,1,1,2)        
        
        self.freeText.textChanged.connect(parent.freeTextChanged)
        self.caseCheckbox.stateChanged.connect(parent.caseCheckChanged)
        self.nullCheckbox.stateChanged.connect(parent.nullCheckChanged)
        self.emptyCheckbox.stateChanged.connect(parent.emptyCheckChanged)
    
    def initOperator(self,operator):
        if operator:
            (value,label) = operator
            index = self.operators.model().findIndex(value)
            self.operators.setCurrentIndex(index)
        else:
            self.operators.reset()
            
    def initRightClause(self,rightClause):
        #rightClause peut-etre soit columnItem soit un texte libre
        if isinstance(rightClause,str) or isinstance(rightClause,unicode) or isinstance(rightClause,Decimal):
            self.freeText.setText(unicode(rightClause)) 
            self.otherFields.clearSelection()           
        else:
            index = self.otherFields.model().findIndex(rightClause)
            self.otherFields.setCurrentIndex(index)
            self.freeText.clear()
        
    def initOptions(self,options):                    
        try:                                
            self.caseCheckbox.setChecked(options['caseinsensitive'])                         
        except:
            self.caseCheckbox.setChecked(False)        
        
        if 'null' in options and options['null'] == True:                                
            self.nullCheckbox.setChecked(True)                         
        else:
            self.nullCheckbox.setChecked(False)
            
        if 'empty' in options and options['empty'] == True:                                
            self.emptyCheckbox.setChecked(True)                         
        else:
            self.emptyCheckbox.setChecked(False)
    
                    
class StringEditor(AbstractEditor):
    def __init__(self,fieldsModel,parent=None):
        AbstractEditor.__init__(self,fieldsModel,parent=parent)                
        self.operatorsModel = StringOperatorModel()
        self.operators.setModel(self.operatorsModel)
        proxyModel = FieldFilter (['STR'])
        proxyModel.setSourceModel(fieldsModel)
        self.otherFields.setModel(proxyModel)
        s1 = self.operators.selectionModel()
        s1.selectionChanged.connect(parent.operatorClicked)
        self.caseCheckbox.show()        
        s2 = self.otherFields.selectionModel()
        s2.selectionChanged.connect(parent.otherFieldsClicked)
            
class NumericEditor(AbstractEditor):
    def __init__(self,fieldsModel,parent=None):
        AbstractEditor.__init__(self,fieldsModel,parent=parent)                
        self.operatorsModel = NumericOperatorModel()
        self.operators.setModel(self.operatorsModel)
        proxyModel = FieldFilter (['DEC','INT'])
        proxyModel.setSourceModel(fieldsModel)
        self.otherFields.setModel(proxyModel)
        s1 = self.operators.selectionModel()
        s1.selectionChanged.connect(parent.operatorClicked)
        s2 = self.otherFields.selectionModel()
        s2.selectionChanged.connect(parent.otherFieldsClicked)
        
class BooleanEditor(AbstractEditor):
    def __init__(self,fieldsModel,parent=None):
        AbstractEditor.__init__(self,fieldsModel,parent=parent)                
        self.operatorsModel = BooleanOperatorModel()
        self.operators.setModel(self.operatorsModel)
        proxyModel = FieldFilter (['BOOL'])
        proxyModel.setSourceModel(fieldsModel) 
        self.otherFields.setModel(proxyModel) 
        s1 = self.operators.selectionModel()
        s1.selectionChanged.connect(parent.operatorClicked)
        s2 = self.otherFields.selectionModel()
        s2.selectionChanged.connect(parent.otherFieldsClicked)
        
        
class OtherEditor(AbstractEditor):
    def __init__(self,fieldsModel,parent=None):
        AbstractEditor.__init__(self,fieldsModel,parent=parent)                
        self.operatorsModel = AllOperatorModel()
        self.operators.setModel(self.operatorsModel)        
        self.otherFields.setModel(fieldsModel)
        s1 = self.operators.selectionModel()
        s1.selectionChanged.connect(parent.operatorClicked)
        s2 = self.otherFields.selectionModel()
        s2.selectionChanged.connect(parent.otherFieldsClicked)


class DateEditor(AbstractEditor):
    def __init__(self,fieldsModel,parent=None):
        AbstractEditor.__init__(self,fieldsModel,parent=parent)                
        self.operatorsModel = TemporalOperatorModel()
        self.operators.setModel(self.operatorsModel)
        proxyModel =  FieldFilter (['DATE','DATETIME'])
        proxyModel.setSourceModel(fieldsModel)
        self.otherFields.setModel(proxyModel)
        s1 = self.operators.selectionModel()
        s1.selectionChanged.connect(parent.operatorClicked)
        s2 = self.otherFields.selectionModel()
        s2.selectionChanged.connect(parent.otherFieldsClicked)
         
class TimeEditor(AbstractEditor):
    def __init__(self,fieldsModel,parent=None):
        AbstractEditor.__init__(self,fieldsModel,parent=parent)                
        self.operatorsModel = TemporalOperatorModel()
        self.operators.setModel(self.operatorsModel)
        proxyModel =  FieldFilter (['TIME','DATETIME'])
        proxyModel.setSourceModel(fieldsModel)
        self.otherFields.setModel(proxyModel)
        s1 = self.operators.selectionModel()
        s1.selectionChanged.connect(parent.operatorClicked)
        s2 = self.otherFields.selectionModel()
        s2.selectionChanged.connect(parent.otherFieldsClicked)

    
        
class ChooseFieldsWidget(QWidget):
    def __init__(self,fieldsModel,whereEditor,parent=None):
        QWidget.__init__(self,parent)
        self.whereEditor = whereEditor
        layout = QGridLayout()
        self.setLayout(layout)
        
        self.allfields = QListView()        
        self.allfields.setModel(fieldsModel)        
        
        self.otherEditor = OtherEditor(fieldsModel,parent=self)
        self.stringEditor = StringEditor(fieldsModel,parent=self)
        self.timeEditor = TimeEditor(fieldsModel,parent=self)
        self.dateEditor = DateEditor(fieldsModel,parent=self)
        self.booleanEditor = BooleanEditor(fieldsModel,parent=self)
        self.numericEditor = NumericEditor(fieldsModel,parent=self)
        
        self.emptyEditor = QFrame()
        
        self.stackedEditors = QStackedLayout()
        self.stackedEditors.addWidget(self.emptyEditor)
        self.stackedEditors.addWidget(self.otherEditor)
        self.stackedEditors.addWidget(self.stringEditor)
        self.stackedEditors.addWidget(self.timeEditor)
        self.stackedEditors.addWidget(self.dateEditor)
        self.stackedEditors.addWidget(self.booleanEditor)
        self.stackedEditors.addWidget(self.numericEditor)
        self.stackedEditors.setContentsMargins(0,0,0,0)
                
        layout.addWidget(self.allfields,0,0)
        layout.addLayout(self.stackedEditors,0,1)
        self.stackedEditors.setCurrentWidget(self.emptyEditor)
        s1 = self.allfields.selectionModel()
        s1.selectionChanged.connect(self.fieldClicked)
        
    def operatorClicked(self,index,index2):
        clause = self.whereEditor.currentClause()
        if clause:
            ind = self.stackedEditors.currentWidget().operators.currentIndex()
            
            if ind.isValid():
                clause.setOperator(ind.data(Qt.EditRole))
                    
    def initValues(self,leftClause,operator,rightClause): #options peut etre
        if leftClause:
            #change the editor
            self.showEditor(leftClause)            
                
            indexLeftClause = self.allfields.model().findIndex(leftClause)                
            self.allfields.setCurrentIndex(indexLeftClause)
        else:
            self.allfields.reset()
            self.stackedEditors.setCurrentWidget(self.emptyEditor)
    
        
            
    def showEditor(self,field): 
        if not field :
            self.stackedEditors.setCurrentWidget(self.emptyEditor)
        elif field.column['type'] == 'STR':
            self.stackedEditors.setCurrentWidget(self.stringEditor)                        
        elif field.column['type'] == 'TIME' or field.column['type'] == 'DATETIME' :
            self.stackedEditors.setCurrentWidget(self.timeEditor)
        elif field.column['type'] == 'DATE':
            self.stackedEditors.setCurrentWidget(self.dateEditor)   
        elif field.column['type'] == 'BOOL':
            self.stackedEditors.setCurrentWidget(self.booleanEditor)         
        elif field.column['type'] == 'DEC' or field.column['type'] == 'INT':
            self.stackedEditors.setCurrentWidget(self.numericEditor)
        else:
            self.stackedEditors.setCurrentWidget(self.otherEditor)
        
        if self.stackedEditors.currentWidget()!=self.emptyEditor and self.whereEditor.currentClause():
            self.stackedEditors.currentWidget().initOperator(self.whereEditor.currentClause().operator)
            self.stackedEditors.currentWidget().initRightClause(self.whereEditor.currentClause().rightClause)
            self.stackedEditors.currentWidget().initOptions(self.whereEditor.currentClause().options)
        
    def fieldClicked(self,index1,index2):
        #change editor
        c = self.whereEditor.currentClause()
        if c:
            ind = self.allfields.currentIndex()
            if ind:
                field = ind.data(Qt.EditRole)
                c.setLeftClause(field)
                self.showEditor(field)
                
            else :
                c.setLeftClause(None)
            
    def otherFieldsClicked(self,index,index2):              
        oldState = self.stackedEditors.currentWidget().freeText.blockSignals(True)
        self.stackedEditors.currentWidget().freeText.clear()
        self.stackedEditors.currentWidget().freeText.blockSignals(oldState)
        
        oldState = self.stackedEditors.currentWidget().nullCheckbox.blockSignals(True)
        self.stackedEditors.currentWidget().nullCheckbox.setChecked(False)
        self.stackedEditors.currentWidget().nullCheckbox.blockSignals(oldState)
        
        oldState = self.stackedEditors.currentWidget().emptyCheckbox.blockSignals(True)
        self.stackedEditors.currentWidget().emptyCheckbox.setChecked(False)
        self.stackedEditors.currentWidget().emptyCheckbox.blockSignals(oldState)
        
        c = self.whereEditor.currentClause()
        if c:
            ind = self.stackedEditors.currentWidget().otherFields.currentIndex()
            if ind:
                field =  ind.data(Qt.EditRole)
                c.setRightClause(field)
        
    
    def emptyCheckChanged(self,value):        
        oldState = self.stackedEditors.currentWidget().freeText.blockSignals(True)
        self.stackedEditors.currentWidget().freeText.clear() 
        self.stackedEditors.currentWidget().freeText.blockSignals(oldState)
        
        oldState = self.stackedEditors.currentWidget().otherFields.blockSignals(True)       
        self.stackedEditors.currentWidget().otherFields.reset()                
        self.stackedEditors.currentWidget().otherFields.blockSignals(oldState)
        
        if Qt.Checked == value:
            oldState = self.stackedEditors.currentWidget().nullCheckbox.blockSignals(True)       
            self.stackedEditors.currentWidget().nullCheckbox.setChecked(False)               
            self.stackedEditors.currentWidget().nullCheckbox.blockSignals(oldState)
        
        currentClause = self.whereEditor.currentClause()
        if currentClause:
            if Qt.Checked == value:
                ischecked = True
            else:
                ischecked = False
                 
            currentClause.setOption('empty',ischecked)
            
            if ischecked: 
                currentClause.setOption('null',False)
    
    #preventCheckStateChanged
    def nullCheckChanged(self,value):
        #self.nullCheckboxIsWorking = True
        
        oldState = self.stackedEditors.currentWidget().freeText.blockSignals(True)
        self.stackedEditors.currentWidget().freeText.clear() 
        self.stackedEditors.currentWidget().freeText.blockSignals(oldState)
        
        oldState = self.stackedEditors.currentWidget().otherFields.blockSignals(True)       
        self.stackedEditors.currentWidget().otherFields.reset()                
        self.stackedEditors.currentWidget().otherFields.blockSignals(oldState)
        
        if Qt.Checked == value:
            oldState = self.stackedEditors.currentWidget().emptyCheckbox.blockSignals(True)       
            self.stackedEditors.currentWidget().emptyCheckbox.setChecked(False)               
            self.stackedEditors.currentWidget().emptyCheckbox.blockSignals(oldState)
            
        currentClause = self.whereEditor.currentClause()
        if currentClause:
            if Qt.Checked == value:
                ischecked = True
            else:
                ischecked = False
                 
            currentClause.setOption('null',ischecked)
            
            if ischecked: 
                currentClause.setOption('empty',False)
        
                        
            
    def caseCheckChanged(self,value):
        currentClause = self.whereEditor.currentClause()
        if currentClause:
            if Qt.Checked == value:
                ischecked = True
            else:
                ischecked = False
                 
            currentClause.setOption('caseinsensitive',ischecked)
             
     
    
                
    def freeTextChanged(self,v):                      
        oldState = self.stackedEditors.currentWidget().nullCheckbox.blockSignals(True)
        self.stackedEditors.currentWidget().nullCheckbox.setChecked(False)           
        self.stackedEditors.currentWidget().nullCheckbox.blockSignals(oldState)
        
        oldState = self.stackedEditors.currentWidget().emptyCheckbox.blockSignals(True)
        self.stackedEditors.currentWidget().emptyCheckbox.setChecked(False)           
        self.stackedEditors.currentWidget().emptyCheckbox.blockSignals(oldState)
        
        c = self.whereEditor.currentClause()
        if c:
            text = self.stackedEditors.currentWidget().freeText.text()
            #check if decimal
            
            try:
                text = Decimal(text)
            except Exception as e:
                print "freeTextChanged error ",e
                pass
            c.setRightClause(text)
         
        if v:
            oldState = self.stackedEditors.currentWidget().otherFields.blockSignals(True)
            self.stackedEditors.currentWidget().otherFields.reset()  
            self.stackedEditors.currentWidget().otherFields.blockSignals(oldState)          
    
class Operator(QComboBox):
    def __init__(self,operatorName,parent = None):  
        QComboBox.__init__(self,parent=parent) 
        self.setMaximumWidth(50)     
        self.setSizePolicy(QSizePolicy.Minimum ,QSizePolicy.Minimum)
        self.model = [('??','??'),('ET',_(u'ET')),('OU',_(u'OU'))]                        
         
        self.addItem('??')
        self.addItem(_(u'ET'))
        self.addItem(_(u'OU'))
        
        self.setCurrentIndex(self.getIndex(operatorName))
        self.currentIndexChanged.connect(self.modified)    

    def getIndex(self,op):
        i = 0
        for (u,v) in self.model:
            if u == op : 
                return i
            i = i + 1
            
        return None
    
        
    def modified(self):        
        ti = self.currentIndex()
        (t,w) = self.model[ti]
        
        self.parent().parent().changeOperator(t)
    
    def setText(self,t):            
        self.setCurrentIndex(self.getIndex(t))
    
class OperatorOld(QLabel):    
    def __init__(self,operatorName,parent=None):
        QLabel.__init__(self,operatorName,parent=parent)
        self.font = QFont()
        self.font.setPointSize(10)
        self.font.setBold(True)    
        self.setFont(self.font)
        self.setMaximumHeight(20) 
        self.setMinimumWidth(20)
        self.setMaximumWidth(20)
        self.setMinimumHeight(20)
            
    def contextMenuEvent(self, event):        
        menu = QMenu()
        andOperator = menu.addAction(_(u"ET"))
        orOperator = menu.addAction(_(u"OU"))
        selectedAction = menu.exec_(event.globalPos())
        if selectedAction == andOperator:                    
            self.parent().parent().changeOperator(_(u"ET"))
        elif selectedAction == orOperator:                    
            self.parent().parent().changeOperator(_(u"OU"))
                
                
            
class ListOfClause(QWidget):
    def __init__(self,whereEditor,parent = None):        
        QWidget.__init__(self,parent=parent)
        self.parentListOfClause = parent
        
        self.whereEditor = whereEditor                   
        
        layout = QVBoxLayout()        
        layout.setContentsMargins(0,0,0,0)       
        layout.setSpacing(0) 
        
        f1=QFrame()
        f1.setProperty("withoperator", "??")
        f1.setStyleSheet('QFrame[withoperator="??"] {background-color: rgb(255,255,0);  border-radius: 10px }') #border: 1px solid rouge;
        f1.setLayout(layout)
        self.f1 = f1
        
        biglayout = QVBoxLayout()
        biglayout.addWidget(f1)
        self.setLayout(biglayout)
        f1.setContentsMargins(20,5,20,5)
        
        
        
        
        
        self.layoutClauses = layout
        
        
                 
        self.operatorName = "??"
                        
        
        
        
        layout.addWidget(Clause(whereEditor,parent=self))
        self.setSizePolicy(QSizePolicy.Minimum ,QSizePolicy.Minimum)
    
    def setValue(self,value):
        
        operatorName = value[0]
        self.changeOperator(operatorName)
        for index in range(1,len(value)):
            c = value[index]            
            operator = Operator(self.operatorName,self)
            if c[0] == 'ET' or c[0] == 'OU':
                listclause = ListOfClause(self.whereEditor,parent=self)
                listclause.setValue(c)
                
                self.layoutClauses.addWidget(operator)
                self.layoutClauses.addWidget(listclause)
                
                
            else:
                clause = Clause(self.whereEditor,parent=self)
                try:
                    (leftClause,operatorClause,rightClause,options) = c
                except:
                    print 'erreur setValue : ',c
                clause.setLeftClause(leftClause)
                clause.setOperator(operatorClause)  
                clause.setRightClause(rightClause)
                clause.setAllOptions(options)
                
                self.layoutClauses.addWidget(operator)
                self.layoutClauses.addWidget(clause)
        
        self.removeClause(self.layoutClauses.itemAt(0).widget())  
    
    def isValid(self):
        
        if self.operatorName == '??' and self.layoutClauses.count()>1:
            return ("blockWithoutOperator",self)
        
        
        
        for i in range(self.layoutClauses.count()):            
            wi = self.layoutClauses.itemAt(i)
            w = wi.widget()
            
            if not isinstance(w,Operator): 
                isValid = w.isValid()
                if isValid != True:                
                    return isValid
                
        return True        
    
              
    def getValue(self):
        result=[]
        result.append(self.operatorName)
        
        for i in range(self.layoutClauses.count()):            
            wi = self.layoutClauses.itemAt(i)
            w = wi.widget()
            
            if not isinstance(w,Operator): 
                clause = w.getValue()
                                
                result.append(clause)
                
        return result            
    
    def changeOperator(self,newOperator):        
        self.operatorName = newOperator
        self.setColor()
        for i in range(self.layoutClauses.count()):            
            wi = self.layoutClauses.itemAt(i)
            w = wi.widget()
            
            if isinstance(w,Operator):                
                w.setText(newOperator)
                w.update()
        
    def setColor(self):    
        self.f1.setProperty("withoperator", self.operatorName)
        if self.operatorName == 'ET':
            self.f1.setStyleSheet('QFrame[withoperator="ET"] {background-color: lightblue;  border-radius: 10px }')
        elif self.operatorName == 'OU':
            self.f1.setStyleSheet('QFrame[withoperator="OU"] {background-color: rgb( 129, 165, 148 );  border-radius: 10px }')
        else:
            self.f1.setStyleSheet('QFrame[withoperator="??"] {background-color: rgb( 255,255,0 );  border-radius: 10px }')
        
        
    def insertNewListOfClause(self,where,refClause):
        index = self.layoutClauses.indexOf(refClause)
        
        operator = Operator(self.operatorName,self)
        clause = ListOfClause(self.whereEditor,self)
        
        if where=='before':            
            self.layoutClauses.insertWidget(index,operator)
            self.layoutClauses.insertWidget(index,clause)
        elif where=='after':
            self.layoutClauses.insertWidget(index+1,clause)            
            self.layoutClauses.insertWidget(index+1,operator)
        
        self.whereEditor.setCurrentClause(clause.layoutClauses.itemAt(0).widget())
                 
    def insertNewClause(self,where,refClause):
        index = self.layoutClauses.indexOf(refClause)
        
        
        operator = Operator(self.operatorName,self)
        clause = Clause(self.whereEditor,parent=self)
        
        if where=='before':            
            self.layoutClauses.insertWidget(index,operator)
            self.layoutClauses.insertWidget(index,clause)
        elif where=='after':
            self.layoutClauses.insertWidget(index+1,clause)            
            self.layoutClauses.insertWidget(index+1,operator)
        
        self.whereEditor.setCurrentClause(clause)
            
    def moveClause(self,direction,clause):
        #swap 2 clauses in fact
        index = self.layoutClauses.indexOf(clause)
        if direction=='up' and index == 0:
            return
        
        if direction=='down' and index == self.layoutClauses.count()-1:
            return
        
        
        if direction == 'up':                        
            wi = self.layoutClauses.itemAt(index - 2)            
            precClause = wi.widget()
            self.layoutClauses.insertWidget(index-2,clause)
            self.layoutClauses.insertWidget(index,precClause)
        elif direction == 'down':                        
            wi = self.layoutClauses.itemAt(index + 2)            
            precClause = wi.widget()
            self.layoutClauses.insertWidget(index,precClause)
            self.layoutClauses.insertWidget(index+2,clause)
                
    def removeClause(self,clause):
        #remove the clause and an operator
        if self.layoutClauses.count() == 1:            
            self.layoutClauses.removeWidget(clause)
            clause.hide()
            del clause
            
            if self == self.whereEditor.rootClause:
                # create an empty clause
                emptyClause = Clause(self.whereEditor,parent=self)
                self.layoutClauses.addWidget(emptyClause)
            else:                
                self.parentListOfClause.removeClause(self)
                
            return
        
        index = self.layoutClauses.indexOf(clause)
        if index == 0:                        
            operator = self.layoutClauses.itemAt(1).widget()
        else:
            operator = self.layoutClauses.itemAt(index-1).widget()      
            
        self.layoutClauses.removeWidget(clause)    
        self.layoutClauses.removeWidget(operator)
        
        clause.hide()
        operator.hide()
        del clause
        del operator
        

class Clause(QWidget):
    def __init__(self,whereEditor,leftClause=None,operator=None,rightClause=None,parent=None,options={}): 
        QWidget.__init__(self)    
        
        layout = QHBoxLayout()
        self.setLayout(layout)
        
        self.label = QLabel()
        layout.addWidget(self.label,1)
        
        self.upButton = QPushButton(QIcon(QPixmap(os.path.join(iconPrefix,'filtre/monter2.png'))),'')
        self.upButton.setToolTip(_(u"monter cette clause"))
        self.upButton.clicked.connect(self.moveClauseUp)
        
        
        self.downButton = QPushButton(QIcon(QPixmap(os.path.join(iconPrefix,'filtre/descendre2.png'))),'')
        
        self.downButton.setToolTip(_(u"descendre cette clause"))
        self.downButton.clicked.connect(self.moveClauseDown)
                
        
        self.newClauseAfterButton = QPushButton(QIcon(QPixmap(os.path.join(iconPrefix,'filtre/nouvelleClause2.png'))),'')        
        self.newClauseAfterButton.setToolTip(_(u"insérer une nouvelle clause"))
        self.newClauseAfterButton.clicked.connect(self.insertNewClauseAfter)
        
        
        self.newGroupAfterButton = QPushButton(QIcon(QPixmap(os.path.join(iconPrefix,'filtre/nouveauBloc2.png'))),'')
        self.newGroupAfterButton.setToolTip(_(u"insérer un nouveau bloc"))
        self.newGroupAfterButton.clicked.connect(self.insertNewGroupAfter)
        
        
        self.removeButton = QPushButton(QIcon(QPixmap(os.path.join(iconPrefix,'filtre/supprimer2.png'))),'')
        self.removeButton.setToolTip(_(u"supprimer cette clause"))
        self.removeButton.clicked.connect(self.removeClause)
        
        
        self.upButton.setMaximumWidth(30)
        self.downButton.setMaximumWidth(30)
        
        self.newClauseAfterButton.setMaximumWidth(30)
        
        self.newGroupAfterButton.setMaximumWidth(40)
        self.removeButton.setMaximumWidth(30)
        
        layout.setSpacing(0)
        layout.addWidget(self.newClauseAfterButton,0)
        layout.addWidget(self.newGroupAfterButton,0)
        layout.addWidget(self.upButton,0)
        layout.addWidget(self.downButton,0)
        layout.addWidget(self.removeButton,0)
        
        self.hideButtons(True)
            
        self.whereEditor = whereEditor
                
        self.label.setContentsMargins(0,0,0,0)
         
        self.label.setMaximumHeight(20)
        self.label.setMinimumHeight(20)
                     
        self.leftClause = leftClause
        self.operator = operator
        self.rightClause = rightClause
        self.options = options
        
        
        self.label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self.label.setWordWrap(False)
        
        self.updateMyText()
    
    def isValid(self):
        if self.leftClause is None:
            return ("leftClauseEmpty",self)
        if self.operator is None:
            return ("operatorEmpty",self)
        
        if 'null' in self.options :
            nullvalue = self.options['null']
        else:
            nullvalue = False
        
        if 'empty' in self.options :
            emptyvalue = self.options['empty']
        else:
            emptyvalue = False    
            
        if self.rightClause is None and nullvalue == False and emptyvalue == False:
            return ("rightClauseEmpty",self)
        
        return True
        
    def moveClauseUp(self):
        self.parent().parent().moveClause('up',self)
        
        
    def moveClauseDown(self):
        self.parent().parent().moveClause('down',self)    
        
    def insertNewClauseBefore(self):
        self.parent().parent().insertNewClause('before',self)
        
    def insertNewClauseAfter(self):
        self.parent().parent().insertNewClause('after',self)
        
    def insertNewGroupBefore(self):
        self.parent().parent().insertNewListOfClause('before',self)
        
    def insertNewGroupAfter(self):
        self.parent().parent().insertNewListOfClause('after',self)    
    
    def removeClause(self):
        self.parent().parent().removeClause(self)
            
    def hideButtons(self,isHidden):
        if isHidden:
            self.upButton.hide()
            self.downButton.hide()
            
            self.newClauseAfterButton.hide()
            
            self.newGroupAfterButton.hide()
            self.removeButton.hide()
        
        else:
            self.upButton.show()
            self.downButton.show()
            
            self.newClauseAfterButton.show()
            
            self.newGroupAfterButton.show()
            self.removeButton.show()
    
    def getValue(self):
        return (self.leftClause,self.operator,self.rightClause,self.options)
        
    def setLeftClause(self,clause):
        self.leftClause = clause 
        self.updateMyText()    
    
    def setRightClause(self,clause):
        self.rightClause = clause 
        if clause is not None:
            self.options['null'] = False
            self.options['empty'] = False
            
        self.updateMyText()
    
    def setOperator(self,op):
        self.operator      = op
        self.updateMyText()
    
    def setOption(self,optionName,optionValue):
        self.options[optionName] = optionValue
        if optionName == 'null' or optionName == 'empty':
            if optionValue == True:
                self.rightClause = None 
            
            self.updateMyText()
            
        
    def setAllOptions(self,options):
        self.options = options
                  
    def updateMyText(self):        
        if self.leftClause is not None: 
            left = "%s.%s"%(getTableName(self.leftClause.parentItem()),self.leftClause.column['name'])
        else:
            left=escape(_(u'<vide>'))
                        
        if self.operator is not None:
            (value,label) = self.operator 
            center = label
        else:
            center=escape(_(u'<vide>'))
            
        if self.rightClause is not None: 
            if isinstance(self.rightClause,str) or isinstance(self.rightClause,unicode) or isinstance(self.rightClause,Decimal):
                right = self.rightClause
            else:
                right = "%s.%s"%(getTableName(self.rightClause.parentItem()),self.rightClause.column['name'])
        else:
            if 'null' in self.options and self.options['null'] == True:
                right=escape(_(u'non renseigné'))
            elif 'empty' in self.options and self.options['empty'] == True:
                right=escape(_(u'VIDE'))
            else :
                right=escape(_(u'<vide>'))
                    
        txt = "<span style='color:green'>%s</span> <b>%s</b> <span style='color:green'>%s</span>"%(left,center,right)
        self.label.setText(txt)
        self.label.adjustSize()        
        self.label.updateGeometry()
        self.label.update()
        
    def mousePressEvent(self, event):
        self.whereEditor.setCurrentClause(self)
        
    
    def setSelected(self,isSelected):
        if isSelected:
            self.label.setStyleSheet("background-color:white; border-radius: 0px;")
            self.hideButtons(False)
        else:
            self.label.setStyleSheet("")
            self.hideButtons(True)
            
    def contextMenuEvent(self, event):        
        menu = QMenu()
        insertBeforeCommand = menu.addAction(_(u"insérer une clause avant celle-ci"))
        insertAfterCommand = menu.addAction(_(u"insérer une clause après celle-ci"))
        menu.addSeparator()
        removeCommand = menu.addAction(_(u"effacer cette clause"))
        menu.addSeparator()
        moveUpCommand = menu.addAction(_(u"monter cette clause"))
        moveDownCommand = menu.addAction(_(u"descendre cette clause"))
        menu.addSeparator()
        insertGroupBeforeCommand = menu.addAction(_(u"insérer un nouveau groupe avant"))
        insertGroupAfterCommand = menu.addAction(_(u"insérer un nouveau groupe après"))
        
        selectedAction = menu.exec_(event.globalPos())
        if selectedAction == insertBeforeCommand:                                
            self.parent().parent().insertNewClause('before',self)
        elif selectedAction == insertAfterCommand:                    
            self.parent().parent().insertNewClause('after',self)
        elif selectedAction == insertGroupBeforeCommand:
            self.parent().parent().insertNewListOfClause('before',self) 
        elif selectedAction == insertGroupAfterCommand:
            self.parent().parent().insertNewListOfClause('after',self)     
        elif selectedAction == moveUpCommand:
            self.parent().parent().moveClause('up',self)
        elif selectedAction == moveDownCommand:
            self.parent().parent().moveClause('down',self)    
        elif selectedAction == removeCommand:
            self.parent().parent().removeClause(self)
                                
class WhereEditorWidget(QDialog):
    def __init__(self,allFieldsModel,defaultFilterName,parent=None):
        QDialog.__init__(self)
        self.allFieldsModel = allFieldsModel
        layout = QGridLayout()
        self.setLayout(layout)
        self._currentClause = None
        
        
        label = QLabel(_(u"nom du filtre"))
        self.filterName = QLineEdit(defaultFilterName)
        
        self.whereZone = QScrollArea()
        self.whereZone.setWidgetResizable(True)
        
        
        
                           
        self.rootClause = ListOfClause(self,parent=self) 
        
        
        
        self.rootClause.setContentsMargins(10,10,10,10)
        
        self.whereZone.setWidget(self.rootClause)
        self.whereZone.setAlignment(Qt.AlignCenter)
        
        self.fields = ChooseFieldsWidget(allFieldsModel,self,parent=self)
        
        layout.addWidget(label,0,0)
        layout.addWidget(self.filterName,0,1,1,2)
        
        layout.addWidget(self.whereZone,1,0,1,3)        
        layout.addWidget(self.fields,2,0,1,3)
        
        self.validButton = QPushButton(_(u"valider"))
        self.cancelButton = QPushButton(_(u"annuler"))
        
        layout.addWidget(self.cancelButton,3,0)                                
        layout.addWidget(self.validButton,3,2)
        
        self.validButton.clicked.connect(self.checkIfValid)
        self.cancelButton.clicked.connect(self.reject)
    
        firstClause = self.findFirstClause(self.rootClause)
        
        
        self.setCurrentClause(firstClause)
    
    def findFirstClause(self,ref):                
        w = ref.layoutClauses.itemAt(0).widget()        
        if isinstance(w,Clause):
            return w
        else:
            return self.findFirstClause(w)
            
    def checkIfValid(self):        
        
        if self.filterName.text() is None or len(self.filterName.text().strip()) == 0:    
            self.filterName.setStyleSheet('background-color:red')
            return
        
        ret = self.rootClause.isValid()
        if ret  != True:
            (errorType,obj) = ret
            
            if errorType=='blockWithoutOperator':
                obj.f1.setProperty('withoperator','??')              
                obj.f1.setStyleSheet('QFrame[withoperator="??"] {background-color: rgb( 255,0,0 );  border-radius: 10px }')
            else: #errorType in [leftClauseEmpty/operatorEmpty/rightClauseEmpty]
                self.setCurrentClause(obj)                
                obj.label.setStyleSheet("background-color:red; border-radius: 0px;")
            return
       
        self.accept()    
        
    def result(self):
        return (self.filterName.text(),self.rootClause.getValue())
        
    def setCurrentClause(self,c):
        if self._currentClause:
            self._currentClause.setSelected(False)
            
        self._currentClause = c
        if c:
            self._currentClause.setSelected(True)
            self.fields.initValues(c.leftClause,c.operator,c.rightClause) #pas la peine de mettre options car suel leftclause est utilis�
        
    def currentClause(self):
        return self._currentClause        
        
    
    def setValue(self,label,value):
        self.filterName.setText(label)
        self.rootClause.setValue(value)        
        firstClause = self.findFirstClause(self.rootClause)
        self.setCurrentClause(firstClause)

class FilterModel(QAbstractListModel):
    def __init__(self,filters,parent=None):        
        QAbstractListModel.__init__(self,parent=parent)        
        self.filters = filters
                
    def rowCount(self,parent= QModelIndex()):
        return len(self.filters)
     
    def data(self, index, role = Qt.DisplayRole):        
        if role == Qt.DisplayRole:
            (filter,label) = self.filters[index.row()]                        
            return  label
        elif role == Qt.EditRole :                                            
            return self.filters[index.row()]
        
        return None
    
    def removeFilter(self,index):        
        del self.filters[index]        
        index1 = self.createIndex(0,0,None)
        index2 = self.createIndex(len(self.filters)-1,0,None)
        self.dataChanged.emit(index1,index2)
        
    def addFilter(self, filterName,filterValue):           
        self.filters.append((filterValue,filterName))
        
        index = self.createIndex(len(self.filters)-1,0,None)        
        
        self.dataChanged.emit(index,index)       
        return index
    
    def updateFilter(self,index,filterName,filterValue):
        self.filters[index.row()]=(filterValue,filterName)
                        
        self.dataChanged.emit(index,index)       
        return True

class FiltersList(QListView):    
    def __init__(self,tab,parent=None):        
        QListView.__init__(self,parent=parent)
        self.tab = tab
        
    def mouseDoubleClickEvent(self, event):
        model = FieldsModel(self.tab.view.tablesItem)
        (filter,label) = self.currentIndex().data(Qt.EditRole)
        c = WhereEditorWidget(model,label)
        
        
        c.setValue(label,filter)
        c.raise_()
        response = c.exec_()
        
        if response == QDialog.Accepted:
            (newLabel,newValue) = c.result()
            self.model().updateFilter(self.currentIndex(),newLabel,newValue)
            self.tab.setDirty(True)
            self.tab.setCurrentFilter(newValue)
        
    def contextMenuEvent(self,  event):  
        index = self.indexAt(event.pos())
        if index.row() == 0:
            return   
        menu = QMenu()
        removeAction = menu.addAction(_(u"supprimer le filtre"))            
        selectedAction = menu.exec_(event.globalPos())
        
        if selectedAction == removeAction:                                
            index = self.indexAt(event.pos())
            
            index0 = self.model().createIndex(0,0,None)    
            self.setCurrentIndex(index0) #laurent
        
            (currentFilter,__) = self.currentIndex().data(Qt.EditRole)        
            self.tab.setCurrentFilter(currentFilter)
        
            
            
            self.model().removeFilter(index.row())
            self.tab.setDirty(True)            
            #self.tab.setCurrentFilter(None)                
    
        
    
    
class FiltersWidget(QWidget):
    def __init__(self,tab,startLabelIndex,parent = None):        
        QWidget.__init__(self,parent=parent)
        st='''
        QFrame[withoperator="ET"] {background-color: lightblue;  border-radius: 10px }
        QFrame[withoperator="OU"] {background-color: blue;  border-radius: 10px }
        QFrame[withoperator="none"] {background-color: rgb(0,0,0);  border-radius: 10px }
        '''      
           
        layout = QGridLayout()
        self.setLayout(layout)
        self.tab = tab
        self.startLabelIndex = startLabelIndex
        
        title = QLabel(_(u"Filtres"))
        self.whereList = FiltersList(tab,parent=self)        
        
        self.addFilterButton = QPushButton(QIcon(QPixmap(os.path.join(iconPrefix,'icon_plus.png'))),_(u'Nouveau filtre'))
        
        layout.addWidget(title,0,0)
        layout.addWidget(self.whereList,1,0)        
        layout.addWidget(self.addFilterButton,2,0)
        
        self.whereList.setModel(FilterModel([(None,_(u"aucun filtre"))],parent=self.whereList))
        model = self.whereList.model()
        index = model.createIndex(0,0,None)    
        self.whereList.setCurrentIndex(index) #laurent
        s1 = self.whereList.selectionModel()
        s1.selectionChanged.connect(self.filterChanged)
        self.addFilterButton.clicked.connect(self.addNewFilter)
    
    def addNewFilter(self):
        
        model = FieldsModel(self.tab.view.tablesItem)
        c = WhereEditorWidget(model,_(u'filtre %(num)d')%{'num':self.startLabelIndex})
        c.raise_()
        response = c.exec_()
        if response == QDialog.Accepted:
            (filterName,filterValue) = c.result()
            index = self.whereList.model().addFilter(filterName,filterValue)
            
            self.whereList.setCurrentIndex(index)
            self.startLabelIndex+=1
            
            self.tab.setDirty(True)
            
        
    def filterChanged(self):        
        (currentFilter,__) = self.whereList.currentIndex().data(Qt.EditRole)        
        self.tab.setCurrentFilter(currentFilter)
        
    
        
        
