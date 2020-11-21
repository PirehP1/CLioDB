# -*- coding: utf-8 -*-
"""
.. module:: service
   :synopsis: module 'serveur' des traitements stats et accès aux données 
.. codeauthor:: pireh, amérique du nord, laurent frobert
"""
from PySide import QtGui
import traceback
import os

import sys
import simplejson as json
import time
import datetime
import decimal
import math
import sqlalchemy
from sqlalchemy.engine import create_engine
from sqlalchemy.sql import *
from sqlalchemy.orm import sessionmaker
#from sqlalchemy.sql.expression import Function,_Cast,_Label
from sqlalchemy.sql.expression import _Cast,_Label
from sqlalchemy.sql.functions import Function
import getpass as local
import socket

import logging
import warnings
import numpy as np
import pandas
import scipy.cluster.hierarchy as sch
import scipy.spatial.distance as dist


    
import re
from sqlalchemy.dialects.sqlite import DATETIME,DATE,TIME,VARCHAR
from sqlalchemy import types as sqltypes
import traceback
import sys

def getpath():
    userDocument=QtGui.QDesktopServices.storageLocation(QtGui.QDesktopServices.DocumentsLocation)
    defaultpath = os.path.join(userDocument,'dbexplorer')
    path = None
    
    if os.path.exists("./configpath") :
        try:
            f = open("./configpath",'r')
            path = f.read()
            f.close()
        except:
            path = None
            
    if path is not None:
        return path
    else:
        return defaultpath
        
class Service():
    def __init__(self):
        try:
            
            
            self.dbexplorerConfigPath = getpath()
            
                    
            self.dbStoragePath = os.path.join(self.dbexplorerConfigPath,'storage.sqlite')
            #self.dBengine='url'                
            from dbexplorer.server.storage import initStorageIfNecessary
            initStorageIfNecessary(os.path.join(self.dbexplorerConfigPath,self.dbStoragePath))                        
            self.dbengine = create_engine('sqlite:///'+self.dbStoragePath)
            SqlAlchemySession = sessionmaker(bind=self.dbengine)
            self.dbSession = SqlAlchemySession()
            self.currentDatabase = None
            self.activeDatasource = {}
        except Exception as e:
            logging.exception(e)
    
    
                
        
        
    def getConfigPath(self):
        return self.dbexplorerConfigPath
                
    def isDatasourceNameExists(self,datasourceName):
        from dbexplorer.server.storage import Datasource        
        result = self.dbSession.query(Datasource.id).filter_by(name=datasourceName).first()
        
        if result:
            return True
        else: 
            return False
    
    def getStats(self,conn,selectClause):
        logging.debug('Service server getStats')
        try:
            stats = {}
            resultSet = conn.execute(select([func.count("*")],from_obj=selectClause)).first()        
            (nbRows,) = resultSet
            stats['nbRows'] = nbRows
            stats['cols'] = {}                    
            for col in selectClause.c:                
                s = select([func.count(col),func.count(func.distinct(col)) ],from_obj=selectClause).where(and_(col!=None, func.char_length(self.forceCast(col,'STR'))>0))
                
                resultSet = conn.execute(s).first()
                
                
                (co,distinctco) = resultSet
                
                try:
                    u = unicode(col)
                except:
                    u = unicode(col,'utf8')
                stats[u] = (co,distinctco)
                
            return stats
        except Exception as e:
            logging.error("getStats %s"%(selectClause))
            logging.exception(e)
            
    def saveExploration(self,did,explorationId,name,jsonData):
        logging.debug('Service server saveExploration')
        try:
            from storage import Exploration
            if explorationId == -1:
                #insert            
                ex = Exploration()
                ex.id_datasource = did
                ex.name = name
                ex.document = jsonData
                
                self.dbSession.add(ex)
                self.dbSession.flush()
                self.dbSession.commit()
                return ex.id
            else:
                ex = self.dbSession.query(Exploration).filter_by(id=explorationId).first()
                ex.document = jsonData
                ex.name = name
                self.dbSession.merge(ex)
                self.dbSession.flush()
                self.dbSession.commit()
                return ex.id
        except Exception as e:
            logging.error("Service server, saveExploration, did=%s,explorationId=%s,name=%s,jsonData=%s"%(did,explorationId,name,jsonData))
            logging.exception(e)
        
    def getExplorationDocument(self,explorationId):
        try:
            from storage import Exploration
            ex = self.dbSession.query(Exploration).filter_by(id=explorationId).first()
            return ex.document
        except Exception as e:
            logging.exception(e)
                        
    def getExplorationsNameByDsId(self,datasourceId):
        try:
            from dbexplorer.server.storage import Exploration           
            result = self.dbSession.query(Exploration.id, Exploration.name).filter_by(id_datasource=datasourceId).order_by(Exploration.name).all()
            output = []
            for row in result:
                output.append((row.id,row.name))
                              
            return (None,output)
        except Exception as e:
            logging.exception(e)
        
        
    
    def getDatasource(self,datasourceId,forceRefresh=False):
        from sqlalchemy import MetaData
        from sqlalchemy.engine import reflection
        from sqlalchemy.engine.url import URL
        
        from sqlalchemy import Table
        
        if datasourceId  in self.activeDatasource and not forceRefresh:
            return self.activeDatasource[datasourceId]
        else:
            from dbexplorer.server.storage import Datasource
            ds =  self.dbSession.query(Datasource).filter_by(id=datasourceId).first()
            if not ds:
                return None
            
            convert_unicode = True
            encoding = 'utf8'
            query = ds.query
             
            if ds.engine == 'mysql':
                query={}                  
                query['charset']='utf8'
                query['use_unicode']='1'
                                        
            
                    
                
            url = URL(ds.engine,ds.username,ds.password,ds.host,ds.port,ds.database,query)
            #create connection
            
            try:                
                engine = create_engine(url,encoding=encoding,convert_unicode = convert_unicode)
            except:                
                return None
            self.activeDatasource[datasourceId] = {}
            self.activeDatasource[datasourceId]['engine'] = engine
            
            #get tables name
            insp = reflection.Inspector.from_engine(engine)
            tb = insp.get_table_names()
            views = insp.get_view_names()
            tb = tb+views
            tb.sort()
            
            
            
            self.activeDatasource[datasourceId]['tablesName'] = tb
            
            
            meta = MetaData(bind=engine)
            self.activeDatasource[datasourceId]['tablesModel'] = {}
            self.activeDatasource[datasourceId]['tableStats']={} 
            for tableName in tb:                
                table = Table(tableName, MetaData(), autoload = True, autoload_with = engine)                 
                self.activeDatasource[datasourceId]['tablesModel'][tableName] = table
                                              
                #compute stats for the table and columns
                try :
                    conn = engine.connect()
                    
                    self.activeDatasource[datasourceId]['tableStats'][tableName] = self.getStats(conn,table)                                                                        
                except :
                    traceback.print_exc(file=sys.stdout)                                                         
                finally:
                    conn.close()
                 
            return self.activeDatasource[datasourceId]            
    
    def getNonNaForAColumn(self,ds,tableName,col):                        
        q = select([func.count("*")],from_obj=ds['tablesModel'][tableName]).where(and_(col!=None,  func.length(col) != 0))        
        count_ = ds['engine'].execute(q).first()
        return count_[0]
    
    def getNonNA(self,datasourceId,tableName):        
        try :
            ds = self.getDatasource(datasourceId)
            if not ds:
                return ['error']
            result = []
            for col in ds['tablesModel'][tableName].c :
                count_ = self.getNonNaForAColumn(ds,tableName,col)
                result.append((col.name,count_))
            
            result.sort(lambda x, y: cmp(x[1], y[1]),reverse=True)    
            return result    
        except Exception as e:
            logging.error("getNonNA %s %s"%(datasourceId,tableName))                
            logging.exception(e)                
            return ['error']
    
    def getNAIndividuJointure(self,did,tables,joins,sc,filtre,reverse):        
                                 
        try:
            
            #get the first primardy key from the first jointure or table
            if joins is not None and len(joins)>0:
                firstTableId = joins[0][0]
            else:                
                firstTableId = tables.keys()[0]
            
            
            tableName = tables[firstTableId]['tableName']
            tableAlias = tables[firstTableId]['tableAlias']
            if tableAlias is None or len(tableAlias)==0:
                tableAlias = tableName 
            
            ds = self.getDatasource(did)
            tableModel = ds['tablesModel'][tableName]
            primary_key = tableModel.primary_key
            if primary_key is None or len(primary_key)==0:
                logging.error("NO primary key in getNAIndividuJointure")                                                        
                return (0,[],None)
                
            for f in primary_key:                
                firstPrimaryKey = f
                break
            
                
            primary_key_column_name = "%s__%s"%(tableAlias,firstPrimaryKey.name)     
                                            
                
            result = self.executeQuery(did,tables,joins,sc,filtre,None,None)
            
            nbcol = len(result['header'])
            
            resultset=[]
            line = 1 
            for row in result['resultset']:                                                                   
                c = 0
                index=0
                key_value = None
                for col in row: 
                    if result['header'][index] == primary_key_column_name:
                        key_value = col
                        
                                                
                    if col == None:
                        c += 1
                    elif isinstance(col,str) or isinstance(col,unicode):
                        if len(col) == 0:
                            c += 1
                        elif col.lower() in ['na','n/a']:
                            c += 1
                    index +=1        
                        
                resultset.append((key_value,c))       #line number,count NA                 
                line += 1
                    
                
            resultset.sort(lambda x, y: cmp(x[1], y[1]),reverse=reverse) 
            return (nbcol,resultset,primary_key_column_name)  
        except Exception as e:
            logging.error("getNAIndividuJointure")                
            logging.exception(e)                             
            return (0,[],None)
        
    def getNAJointure(self,did,tables,joins,sc,filtre,reverse):
        try:
            result = self.executeQuery(did,tables,joins,sc,filtre,None,None)
            
            res = len(result['header'])*[0]
            
            for row in result['resultset']:
                for i in range(0,len(row)):
                    if row[i] is None:
                        res[i] = res[i] + 1
                    elif isinstance(row[i],str) and row[i].strip() == '':
                        res[i] = res[i] + 1
                    elif isinstance(row[i],unicode) and row[i].strip() == '':
                        res[i] = res[i] + 1    
            
            resultNA = []
            for i in range(0,len(res)):
                resultNA.append((result['header'][i],res[i]))    
            
            
            #format du resultNA: result.append((col.name,count_))
            resultNA.sort(lambda x, y: cmp(x[1], y[1]),reverse=reverse)    
            return (result['count'],resultNA)  
        except Exception as e:
            logging.error("getNAJointure")                
            logging.exception(e)                             
            return (0,[])
    
    def getNaForAColumn(self,ds,tableName,col):                
        q = select([func.count("*")],from_obj=ds['tablesModel'][tableName]).where(or_(col==None,  func.length(col) == 0))                        
        count_ = ds['engine'].execute(q).first()
        return count_[0]     
              
    def getNA(self,datasourceId,tableName,reverse):        
        try :
            ds = self.getDatasource(datasourceId)
            if not ds:
                return ['error']
            q = select([func.count("*")],from_obj=ds['tablesModel'][tableName])                        
            countTotal = ds['engine'].execute(q).first()[0]
        
            result = []
            for col in ds['tablesModel'][tableName].c :
                count_ = self.getNaForAColumn(ds,tableName,col)                
                result.append((col.name,count_))
            
            result.sort(lambda x, y: cmp(x[1], y[1]),reverse=reverse)    
            
            return (countTotal,result)    
        
        except Exception as e:
            logging.error("getNA %s %s"%(datasourceId,tableName))                
            logging.exception(e)                 
            return ['error']
        
                
    def getFieldsName(self,datasourceId,tableName):
        try :
            ds = self.getDatasource(datasourceId)
            if not ds:
                return ['error']
            result = []
            for col in ds['tablesModel'][tableName].c :
                result.append(col.name)
                
            return result    
        except :
            e = sys.exc_info()[1]                      
            return ['error']
    
    def getTablesNameById(self,datasourceId):        
        try :
            ds = self.getDatasource(datasourceId,forceRefresh=True)
            return None,ds['tablesName']
        except :
            e = sys.exc_info()[1]            
            return e,None
    
        
            
    def getTablesName(self,engine,username,password,host,port,database,query):
        from sqlalchemy import create_engine,MetaData
        from sqlalchemy.engine import reflection
        from sqlalchemy.engine.url import URL
        try :        
            
            if not username:
                username = None
                
            if not password:
                password = None
                
            if not host:
                host = None
                
            if not port :
                port = None
            
            if not database :
                database = None
            
            if not query:
                query = None
            
            url = URL(engine,username,password,host,port,database,query)
            
            engine = create_engine(url)
            insp = reflection.Inspector.from_engine(engine)
            tb = insp.get_table_names()
            tb.sort()
            
            return None,tb 
        except :
            e = sys.exc_info()[1]
        return e,None

    def removeExploration(self,exploId):
        try:
            from dbexplorer.server.storage import Exploration
            explo = self.dbSession.query(Exploration).filter_by(id=exploId).first()
            self.dbSession.delete(explo)            
            self.dbSession.flush()                        
            self.dbSession.commit()
            return 'ok'
        except:
            self.dbSession.rollback()
            return 'ko'
        
    def removeDatasource(self,datasourceId):
        try:
            from dbexplorer.server.storage import Datasource,Exploration
            
            #remove all exploration 
            explos =  self.dbSession.query(Exploration).filter_by(id_datasource=datasourceId)
            for exp in explos:
                self.dbSession.delete(exp)
            
            ds =  self.dbSession.query(Datasource).filter_by(id=datasourceId).first()
            self.dbSession.delete(ds)
            
            self.dbSession.flush()                        
            self.dbSession.commit()
            return 'ok'
        except:
            self.dbSession.rollback()
            return 'ko'
        
    
        
    def newDatasource(self,datasourceInfo): 
        
        (datasourceName,engine,username,password,host,port,database,query) = datasourceInfo
                
                
        from dbexplorer.server.storage import Datasource
        ds = Datasource()        
        ds.name = datasourceName
        ds.database = database
        ds.host = host
        ds.port = port
        ds.username = username
        ds.password = password
        ds.engine = engine
        ds.query = query
        self.dbSession.add(ds)
        self.dbSession.flush()                        
        self.dbSession.commit()
        
        
        return (ds.id,datasourceName)
    
    def getDatasourcesNameList(self):    
        try:            
            from dbexplorer.server.storage import Datasource        
            result = self.dbSession.query(Datasource.id, Datasource.name).order_by(Datasource.name).all()
            output = []
            for row in result:
                output.append((row.id,row.name))
                              
            return output
            
        except:
            return []
        
    def getTableSchema(self,datasourceId,tableName):
        ds = self.getDatasource(datasourceId)
        
        try :        
            stats = ds['tableStats'][tableName]
        except KeyError:
            #print 'KeyError %s not found in %s'%(tableName,ds['tableStats'])
            ds = self.getDatasource(datasourceId,forceRefresh=True)
            try :        
                stats = ds['tableStats'][tableName]
            except KeyError:
                print 'KeyError %s not found in %s'%(tableName,ds['tableStats'])
                return None
        
        tableModel = ds['tablesModel'][tableName]
        
        
        result = {}        
                
        result['tableName'] = tableName
        result['count'] = stats['nbRows']
        result['cols'] = []
        for col in tableModel.c:
            c = {}
            c['name'] = col.name
            
            c['type'],c['typetaille'],c['typeprecision'] = self.getColType(col)
            c['typenatif'] = c['type']
            try:
                u = unicode(col)
            except:
                u = unicode(col,'utf8')
            (c['count'],c['distinctCount']) = stats[u]
            
            c['fks'] = self.getColForeignKeys(col)  
            result['cols'].append(c)
        
        
         
        from dbexplorer.server.storage import Datasource
        response = self.dbSession.query(Datasource.document).filter_by(id=datasourceId).first()        
        if response:
            (jsondoc,) = response
            if jsondoc is not None:
                document = json.loads(jsondoc)
                try:                    
                    for col in document[tableName]['types']:
                        [colName,typenatif,type,count] = col
                        #impacte le nouveau type dans le schema de la table
                        for c in result['cols']:
                            if c['name'] == colName:
                                c['type'] = type
                            
                except:
                    pass
        
        return result
    
    def setTableSchema(self,did,tableName,cols):        
        from dbexplorer.server.storage import Datasource
        ds = self.dbSession.query(Datasource).filter_by(id=did).first()
        if ds:
            jsondoc = ds.document
            if jsondoc is None or jsondoc=='':
                doc={}
            else:
                doc = json.loads(jsondoc)
                
            if tableName not in doc:
                doc[tableName] = {}
                doc[tableName]['types']=[]
            doc[tableName]['types'] = cols
            
            ds.document = json.dumps(doc)
            
            self.dbSession.merge(ds)
            self.dbSession.flush()
            self.dbSession.commit()
                
        pass
    
    
        
    def getColForeignKeys(self,col):
        fks = set([])
        for fk  in col.foreign_keys:
            try:
                u = unicode(fk.column.table)
            except:
                u = unicode(fk.column.table,'utf8')
            tableName = u
            
            try:
                u = unicode(fk.column.name)
            except:
                u = unicode(fk.column.name,'utf8')
            columnName = u
            fks.add((tableName,columnName))
            
        return fks
    
    def getColType(self,col):                  
        try:
            try:
                u = unicode(col.type)
            except:
                try:
                    u = unicode(col.type,'utf8')
                except:
                    u = col.type
            
            
                    
            s = u
           
            try:
                i1 = s.index('(')+1
                i2 = s.index(')')           
                s2 = s[i1:i2]
                if ',' in s2:
                    a,b = s2.split(",")
                    taille,precision = int(a),int(b)
                else:
                    taille,precision = int(s2),-1   
            except:
                taille = -1
                precision = -1
                        
            
                              
            if isinstance(col.type,sqlalchemy.types.Integer) or isinstance(col.type,sqlalchemy.types.SMALLINT):
                return "INT",taille,precision
            elif isinstance(col.type,sqlalchemy.types.String):
                return "STR",taille,precision
            elif isinstance(col.type,sqlalchemy.types.Date):
                return "DATE",taille,precision
            elif isinstance(col.type,sqlalchemy.types.Time):
                return "TIME",taille,precision
            elif isinstance(col.type,sqlalchemy.types.DateTime):
                return "DATETIME",taille,precision
            elif isinstance(col.type,sqlalchemy.types.Numeric):
                return "DEC",taille,precision
            elif isinstance(col.type,sqlalchemy.types.Boolean):
                return "BOOL",taille,precision
            else:                                
                return "STR",taille,precision
        except :            
            
            traceback.print_exc(file=sys.stdout)
        return "STR",-1,-1
    
    
    def average(self,s): 
        return sum(s) / (len(s)*1.0)
    
    def mediane(self,L):
        if not L:
            return None
        
        L.sort()
        N = len(L)
        n = N/2.0
        p = int(n)
        if n == p:
            return (L[p-1]+L[p])*1.0/2.0
        else:
            return L[p]*1.0
    
    
    def getColumnDetailsFromQuery(self,datasourceId,tables,joins,sc,filtre,index):
        tablesTypes = {}
        for tableId in tables:                    
            tablesTypes[tableId] = tables[tableId]['tableTypes']
            
        colinfo = sc[index]   
        tableName = tables[colinfo['tableId']]['tableName']             
        (typenatif,type) = tablesTypes[colinfo['tableId']][colinfo['column']]
        
        ds = self.getDatasource(datasourceId)
        table = ds['tablesModel'][tableName]
        
        sc[index]['newname']='stat_column_alias'
        query = self.getQuery(datasourceId,tables,joins,sc,filtre)
        
        col = 'stat_column_alias'
        
        if type=='DEC' or type == 'INT':
            try:
                result={}                
                s = select(['stat_column_alias, count(*) '],from_obj=query.alias('stat_db_explorer')).group_by(col).order_by(col)                
                data = ds['engine'].execute(s)
                
                values=[]
                mode=None
                maxc=None
                result['distinctvalues']=[]                
                for row in data:
                    (d,c) = row                    
                    result['distinctvalues'].append((d,c))
                    if d is not None:
                        values.append(d)
                        if mode is None:
                            mode = d
                            maxc = c
                        elif c>maxc:
                            mode = d
                            maxc = c
                            
                
                    
                result['min']=min(values)
                result['max']=max(values)
                avg = self.average(values)
                result['avg']=avg
                
                variance = map(lambda x: (x - avg)**2, values)
                
                result['ecart']=math.sqrt(self.average(variance))
                
                result['mediane']=self.mediane(values)
                result['mode']=mode
                result['type'] = type
                
                return result
            except Exception as e:                
                logging.exception(e)
                return {'type':type,'min':0,'max':0,'ecart':0,'avg':0,'mediane':0,'mode':0}
        elif type=='DATE' or type=='DATETIME':
            try:
                result={}                                   
                s = select(['stat_column_alias, count(*)'],from_obj=query.alias('stat_db_explorer')).group_by(col).order_by(col)     
                data = ds['engine'].execute(s)
                
                values=[]
                mode=None
                maxc=None
                result['distinctvalues']=[]
                for row in data:
                    (d,c) = row
                    try:
                        u = unicode(d)
                    except:
                        u = unicode(d,'utf8')
                    result['distinctvalues'].append((u,c))
                    if d:
                        values.append(d)
                        if not mode:
                            mode = d
                            maxc = c
                        elif c>maxc:
                            mode = d
                            maxc = c
                            
                
                    
                result['min']=min(values)
                result['max']=max(values)
                from matplotlib.dates import date2num,num2date
                
                valuesNum = map(lambda x:date2num(x), values)
                
                avg = self.average(valuesNum)
                
                result['avg']=num2date(avg)
                
                med = self.mediane(valuesNum)
                result['mediane']=num2date(med)
                
                result['mode']=mode
                result['type'] = type
                
                return result
            except Exception as e:
                logging.exception(e)
                return {'type':type,'min':0,'max':0,'mode':0,'avg':0,'mediane':0}
                
        else:    
            if type=='STR':
                tri=func.lower(col)
            else:
                tri = col
                            
            s = select(['stat_column_alias, count(*)'],from_obj=query.alias('stat_db_explorer')).group_by(col).order_by(tri)
            
            data = ds['engine'].execute(s)
            
            result={}
            result['distinctvalues']=[]
            for row in data:
                (d,c) = row            
                try:
                    u = unicode(d)
                except:                    
                    u = unicode(d,'utf8')
                result['distinctvalues'].append((u,c))
                
            result['type'] = type       
            return result
        
        
        
            
            
        
    
    def getColumnDetails(self,dsId,tableName,columnName,typenatif,type) : 
         
        ds = self.getDatasource(dsId)
        table = ds['tablesModel'][tableName]
        col = table.c[columnName]
        if typenatif!=type:            
            col = self.forceCast(col,type)
        
        
        if type=='DEC' or type == 'INT':
            try:
                result={}                
                s = select([col,func.count('*')],from_obj=table).group_by(col).order_by(col)       
                data = ds['engine'].execute(s)
                
                values=[]
                mode=None
                maxc=None
                result['distinctvalues']=[]
                for row in data:
                    (d,c) = row                    
                    result['distinctvalues'].append((d,c))
                    if d is not None:
                        values.append(float(d))
                        if mode is None:
                            mode = d
                            maxc = c
                        elif c>maxc:
                            mode = d
                            maxc = c
                            
                
                    
                result['min']=min(values)
                result['max']=max(values)
                avg = self.average(values)
                result['avg']=avg
                
                variance = map(lambda x: (x - avg)**2, values)
                
                result['ecart']=math.sqrt(self.average(variance))
                
                result['mediane']=self.mediane(values)
                result['mode']=mode
                result['type'] = type
                
                return result
            except Exception as e:
                logging.exception(e)
                return {'type':type,'min':0,'max':0,'ecart':0,'avg':0,'mediane':0,'mode':0}
        elif type=='DATE' or type=='DATETIME':
            try:
                result={}                
                s = select([col,func.count('*')],from_obj=table).group_by(col).order_by(col)       
                data = ds['engine'].execute(s)
                
                values=[]
                mode=None
                maxc=None
                result['distinctvalues']=[]
                for row in data:
                    (d,c) = row
                    try:
                        u = unicode(d)
                    except:
                        u = unicode(d,'utf8')
                    result['distinctvalues'].append((u,c))
                    if d:
                        values.append(d)
                        if not mode:
                            mode = d
                            maxc = c
                        elif c>maxc:
                            mode = d
                            maxc = c
                            
                
                    
                result['min']=min(values)
                result['max']=max(values)
                from matplotlib.dates import date2num,num2date
                
                valuesNum = map(lambda x:date2num(x), values)
                
                avg = self.average(valuesNum)
                
                result['avg']=num2date(avg)
                
                med = self.mediane(valuesNum)
                result['mediane']=num2date(med)
                result['mode']=mode
                result['type'] = type
                
                return result
            except Exception as e:
                logging.exception(e)
                return {'type':type,'min':0,'max':0,'mode':0}
                
        else:    
            if type=='STR':
                tri=func.lower(cast(col,sqlalchemy.types.VARCHAR)) 
            else:
                tri = col
            
            
            s = select([col,func.count('*')],from_obj=table).group_by(col).order_by(tri)       
            data = ds['engine'].execute(s)
            
            result={}
            result['distinctvalues']=[]
            for row in data:
                (d,c) = row            
                try:
                    u = unicode(d)
                except:                    
                    u = unicode(d,'utf8')
                result['distinctvalues'].append((u,c))
                 
            result['type'] = type      
            return result        
    
    
    
    def buildFilter(self,value,aliases,tableTypes=None):        
        filter=[]
        for index in range(1,len(value)):
            c = value[index]                        
            if c[0] == 'ET' or c[0] == 'OU':
                filter.append(self.buildFilter(c,aliases))                                                
            else:                
                try:
                    [leftTableId,leftColumnName,operatorId,rightTableId,rightColumnName,options] = c
                except:
                    [leftTableId,leftColumnName,operatorId,rightTableId,rightColumnName] = c
                    options={}
                
                leftcol =  self.castIfNecessary(leftTableId,leftColumnName,tableTypes,aliases[leftTableId].c[leftColumnName])    
                                    
                if rightTableId == None and rightColumnName == None:
                    rightcol = None                    
                elif  rightTableId!=-1:
                    rightcol =  self.castIfNecessary(rightTableId,rightColumnName,tableTypes,aliases[rightTableId].c[rightColumnName])                     
                else :
                    rightcol = rightColumnName
                
                try:
                    (type,_,_  )= self.getColType(leftcol)
                    if options['caseinsensitive'] == True and type=='STR' and rightcol != None:
                        leftcol = func.lower(leftcol)
                        rightcol = func.lower(rightcol)
                except:
                    pass
                
                if rightcol is None and options['empty'] == False:                    
                    if operatorId == '!=':
                        filter.append(leftcol != None)
                    elif operatorId == '=' :
                        filter.append(leftcol == None)
                    else:
                        filter.append(leftcol.op(operatorId)(rightcol))
                           
                elif rightcol is None and options['empty'] == True:                    
                    if operatorId == '!=':
                        filter.append(leftcol != '')
                    elif operatorId == '=' :
                        filter.append(leftcol == '')
                    else:
                        filter.append(leftcol.op(operatorId)(''))
                                 
                elif operatorId == 'contains':
                    filter.append(leftcol.contains(rightcol))
                elif operatorId == 'startswith':
                    filter.append(leftcol.startswith(rightcol))
                elif operatorId == 'endswith':
                    filter.append(leftcol.endswith(rightcol))        
                else:                    
                    if isinstance(rightcol, decimal.Decimal) and rightcol % 1 == 0: # nombre entier
                        colvalue =  int(rightcol)
                    else:
                        colvalue = rightcol
                            
                    valx = leftcol.op(operatorId)(colvalue)                            
                    filter.append(valx)
                    
                
        operatorName = value[0]
        if operatorName == 'ET':
            return and_(*filter)
        else:
            return or_(*filter)        
        
    def getModalite(self,datasourceId,query,col):
        query2 = select(['distinct %s '%(col._label,)],from_obj=query.apply_labels().alias('burt')).order_by(col._label) 
        ds  = self.getDatasource(datasourceId)
        data = ds['engine'].execute(query2)
        
                
        return data
        
    def addLabelToCastField(self,tables,sc):
        
        index=0
        for s in sc:
            tableType = tables[s['tableId']]['tableTypes']
            (natifType,newType) = tableType[s['column']]
            if natifType != newType and len(s['newname']) == 0:
                s['newname'] = 'dbexplorer_anon_%d'%(index)
                index += 1
                
    def getDataScatterPlot(self,datasourceId,tables,joins,selectedColumns,filtre):
        try:
            ds  = self.getDatasource(datasourceId)
            query = self.getQuery(datasourceId,tables,joins,selectedColumns,filtre)
            data = ds['engine'].execute(query)
            
            nomColonnes=[]
            
            for t in data._cursor_description():                
                try:
                    u = unicode(t[0])
                except:
                    u = unicode(t[0],'utf8')
                    
                nomColonnes.append(u)
                
            
            result = []
            types = []
            isFirstElem = True
            for i in range(len(nomColonnes)):
                result.append([])
                types.append('other')
                
            from matplotlib.dates import date2num        
            for r in data:                
                
                for i in range(len(nomColonnes)):
                    if r[i] is not None:                            
                        if isinstance(r[i],datetime.date) :
                            types[i] = "date"
                        elif isinstance(r[i],datetime.datetime):
                            types[i] = "datetime"
                        else:
                            types[i] = 'other'    
                    
                        
                for i in range(len(nomColonnes)):
                    if isinstance(r[i],datetime.date) or isinstance(r[i],datetime.datetime):
                        u = date2num(r[i]) 
                        u = r[i]                
                    else:
                        u = r[i]
                    result[i].append(u)
            
            
            warnings.filterwarnings('error')
            arrays = []
            for i in range(len(nomColonnes)):
                arrays.append(np.array(result[i]))
                
            dat=np.array(arrays)
                
            
            return dat,nomColonnes,types
        except:
            import traceback
            import sys
            traceback.print_exc(file=sys.stdout)
            return np.array([]),[],[]
        finally:            
            warnings.filterwarnings('ignore')
                             
    def getDataframe(self,datasourceId,tables,joins,selectedColumns,filtre):
        try:
            ds  = self.getDatasource(datasourceId)
            query = self.getQuery(datasourceId,tables,joins,selectedColumns,filtre)
            data = ds['engine'].execute(query)
                
            nomColonnes=[]
            for t in selectedColumns:
                nomCol = t['column']
                tableId = t['tableId']
                table = tables[tableId]
                
                nomTable = table['tableAlias'] or table['tableName'] 
                nomColonnes.append("%s/%s"%(nomTable,nomCol))
                
            
            from pandas import DataFrame
            result=[]
            warnings.filterwarnings('error')
            for row in data:                
                r=[]
                for col in row:      
                    if col is None:
                        u = None
                    else:
                        '''       
                        try:
                            print col
                            print col.__class__
                        except:
                            pass
                        '''
                               
                        if col and isinstance(col, decimal.Decimal):
                            u = col
                        elif isinstance(col, datetime.datetime): 
                            
                            
                            t = (col -datetime.datetime(1000,1,1))
                            u = (t.microseconds + (t.seconds + t.days * 24 * 3600) * 10**6) / 10**6
                        elif isinstance(col, datetime.date):
                            t = (col -datetime.date(1000,1,1))
                            u = (t.microseconds + (t.seconds + t.days * 24 * 3600) * 10**6) / 10**6
                            
                        
                                                        
                        else:
                            try:
                                u = unicode(col)
                            except:
                                u = unicode(col,'utf8')
                                
                        
                    r.append(u)
                result.append(r)
                
            df = DataFrame(result )
            df.columns = nomColonnes
            #df.index = range(0,len(df.values))
            df.index = range(0,len(result))
            return df
        except:
            
            traceback.print_exc(file=sys.stdout)
            return DataFrame()
        finally:            
            warnings.filterwarnings('ignore')    
            
    def getBurt(self,datasourceId,tables,joins,selectedColumns,filtre):
        try:
            self.getDataframe(datasourceId,tables,joins,selectedColumns,filtre)
            
            ds  = self.getDatasource(datasourceId)
            query = self.getQuery(datasourceId,tables,joins,selectedColumns,filtre)
            data = ds['engine'].execute(query)
            
            
            nomColonnes=[]
            
            
            for t in data._cursor_description():
                try:
                    u = unicode(t[0])
                except:
                    u = unicode(t[0],'utf8')
                    
                nomColonnes.append(u)
            
            
            data = ds['engine'].execute(query)
            modalites={}
            values={}
            
            for row in data:
                for n in range(len(nomColonnes)):
                    if nomColonnes[n] not in modalites:
                        modalites[nomColonnes[n]]  = []
                    
                    try:
                        u = unicode(row[n])
                    except:
                        try:
                            u = unicode(row[n],'utf8')
                        except:
                            u = row[n]
                            
                    modalites[nomColonnes[n]].append(u)
                
                rang = range(0,len(nomColonnes))
                while rang:
                    elem = rang[0]
                    for i in rang:
                        try:
                            u1 = unicode(row[elem])
                        except:
                            try:
                                u1 = unicode(row[elem],'utf8')
                            except:
                                u1 = row[elem]
                        
                        try:
                            u2 = unicode(row[i])
                        except:
                            try:
                                u2 = unicode(row[i],'utf8')
                            except:
                                u2 = row[i]        
                                
                        key = ((nomColonnes[elem],u1),(nomColonnes[i],u2))
                        if key not in values:
                            values[key] = 0
                        values[key] += 1
                    rang.pop(0)    
                    
                    
                
            #remove duplicates
            for m in modalites:
                modalites[m] = sorted(set(modalites[m]))  
            
            #print modalites      
        except Exception as e:
            print 'error : ',e
            traceback.print_exc(file=sys.stdout) 
            
        
       
        
        
        return   {'values':values,'modalites':modalites,'nomColonnes':nomColonnes}
    
    def isNewTypeValid(self,datasourceId,tableName,colname,newtype):
        ds  = self.getDatasource(datasourceId)
        table = ds['tablesModel'][tableName]
        col = table.c[colname]
        
        mauvais_transtypage = []
        
        from datetime import date
        if newtype in ['INT','DEC','BOOL','STR','DATE','TIME','DATETIME']:
            q = select([self.forceCast(col, 'STR')],from_obj=table) 
            
            result = ds['engine'].execute(q)
            for r in result:
                try:
                    val = r[0] 
                    if val is not None:
                        if newtype=='INT':
                            x = int(val)
                        elif newtype=='DEC':
                            x = float(val)
                        elif newtype=='BOOL':
                            if val not in [0,1,'0','1']:
                                raise Exception('type error')    
                        elif newtype=='STR':
                            pass # toujours ok le STR                        
                        elif newtype=='DATE':                                                        
                            x = datetime.datetime.strptime(val,"%Y-%m-%d").date() 
                        elif newtype=='TIME':                                                        
                            x = datetime.datetime.strptime(val,"%H:%M:%S").time()
                        elif newtype=='DATETIME':                                                        
                            x = datetime.datetime.strptime(val,"%Y-%m-%d %H:%M:%S")
                                    
                except Exception as e:
                    #print e
                    mauvais_transtypage.append(r[0])
            result.close()    
            
        if len(mauvais_transtypage)>0:
            return False,list(set(mauvais_transtypage))
            
        return True,[]
    
            
    def getSampleData(self,datasourceId,tableName,columnName):
        ds  = self.getDatasource(datasourceId)
        table = ds['tablesModel'][tableName]
        col = table.c[columnName]
        q = select([col],from_obj=table).where(and_(col!=None,  func.length(col) != 0)).limit(10)
           
        result = ds['engine'].execute(q)
        data=[]
        for r in result:
            col = r[0]
            try:
                u = unicode(col)
            except:
                try:
                    u = unicode(col,'utf8')
                except:
                    u = str(col)
            data.append(u)
        
        result.close()
        
        return data
     
    def getBurtOld(self,datasourceId,tables,joins,selectedColumns,filtre):        
        self.addLabelToCastField(tables,selectedColumns)
        query = self.getQuery(datasourceId,tables,joins,selectedColumns,filtre)        
        cs = query._raw_columns
        
          
        values = {}
        
        modalites={}        
        nomColonnes=[]
        for col in cs:
            
            if isinstance(col,_Label) :
                if col.__dict__['_label'].startswith('dbexplorer_anon_'):                      
                    nomcol = unicode(col.__dict__['_element'].__dict__['clause'])
                else:
                    nomcol = unicode(col.__dict__['_label'])
            else:
                nomcol = unicode(col)
            nomColonnes.append(nomcol)
                        
            mods = self.getModalite(datasourceId,query,col)
            modalites[nomcol] = []            
            for row in mods:
                for c in row:                    
                    modalites[nomcol].append(unicode(c))                     
            #print 'get modalites pour col',nomcol,modalites[nomcol]
        
             
        
        rang = range(0,len(cs))
        #calcul de la matrice pour chaque variables (2 a 2)
        while rang:
            #elem = rang.pop(0)
            elem = rang[0]
            for i in rang:
                try:                                         
                    query2 = select([cs[elem]._label,cs[i]._label,func.count('*')],from_obj=query.apply_labels().alias('burt')).group_by(cs[elem]._label,cs[i]._label)                
                    ds  = self.getDatasource(datasourceId)                    
                    data = ds['engine'].execute(query2)
                    
                                        
                    if isinstance(cs[elem],_Label):
                        if cs[elem]._label.startswith('dbexplorer_anon_'): 
                                                                    
                            nomCol1 = unicode(cs[elem]._element.__dict__['clause'])
                        else:                            
                            nomCol1 = unicode(cs[elem]._label)
                    else:
                        nomCol1 = unicode(cs[elem])
                    
                    if isinstance(cs[i],_Label):
                        if cs[i]._label.startswith('dbexplorer_anon_'):                                                  
                            nomCol2 = unicode(cs[i]._element.__dict__['clause'])
                        else:                            
                            nomCol2 = unicode(cs[i]._label)
                    else:
                        nomCol2 = unicode(cs[i])
                    
                    
                    
                    indexNomCol1 = nomColonnes.index(nomCol1)
                    indexNomCol2 = nomColonnes.index(nomCol2)
                    
                    g=0
                    for (mod1,mod2,val) in data:                        
                        values[((nomCol1,unicode(mod1)),(nomCol2,unicode(mod2)))] = unicode(val)
                        
                        
                except :                
                    e = sys.exc_info()[1]
                    print 'ERROR',e
                    traceback.print_exc(file=sys.stdout)
                    
            rang.pop(0)
                    
                 
        result =  {'values':values,'modalites':modalites,'nomColonnes':nomColonnes}                
        
        return result 
        
    def exportCustomSQLToCsv(self,datasourceId,sql,filename):
        import dbexplorer.client.ucsv as csv
        ds  = self.getDatasource(datasourceId)
        with open(filename, 'wb') as outfile:        
            outcsv = csv.writer(outfile)
            records = ds['engine'].execute(sql)
            outcsv.writerow(records.keys())
            for curr in records:
                newcurr=[]
                for field in curr:                    
                    if field is None:
                        field=''
                    newcurr.append(field)                    
                outcsv.writerow(newcurr)
            # or maybe use outcsv.writerows(records)
            outfile.flush()
            outfile.close()
            outfile = None
            
        
    def createView(self,did,nomVue,sql):
        ds  = self.getDatasource(did)
        try :             
            ds['engine'].execute("create view %s as %s"%(nomVue,sql))
            return None        
        except Exception as e:
            return e    
        
        
        
        
    def executeCustomSQL(self,datasourceId,sql):
        ds  = self.getDatasource(datasourceId)
        try :             
            data = ds['engine'].execute(sql)
            resultSet=[]
            for row in data:
                resultSet.append(row)
                
            return {'columnsName':data._metadata.keys,'resultset':resultSet,'error':None}
        
        except Exception as e:
            return {'resultset':None,'error':e}    
    
    def getNAIndividu(self,datasourceId,tables,joins,selectedColumns,filtre,reverse):
        ds  = self.getDatasource(datasourceId)
        query = self.getQuery(datasourceId,tables,joins,selectedColumns,filtre)        
        result={}
        result['resultset']=[]
        result['nbcol'] = 0
        try :                         
            data = ds['engine'].execute(query)
            line = 1
            for row in data:
                
                c = 0
                for col in row: 
                    if line == 1:
                        result['nbcol'] +=1  
                    
                    if col == None:
                        c += 1
                    elif isinstance(col,str) or isinstance(col,unicode):
                        if len(col) == 0:
                            c += 1
                        elif col.lower() in ['na','n/a']:
                            c += 1
                            
                        
                result['resultset'].append((line,c))       #line number,count NA                 
                line += 1
                
            
            result['resultset'].sort(lambda x, y: cmp(x[1], y[1]),reverse=reverse) 
            return result
        
        except :            
            e = sys.exc_info()[1]
            print e            
            result['nbcol'] = 0
            result['resultset'] = []
            return result
        
        
    def executeQuery(self,datasourceId,tables,joins,selectedColumns,filtre,thelimit,theoffset):        
        ds  = self.getDatasource(datasourceId)
        query = self.getQuery(datasourceId,tables,joins,selectedColumns,filtre)   
        #print "query is",query     
        result={}
        result['query'] = self.getquerystring(query,ds['engine'])
        conn = None
        try :             
                        
            
            import threading
            
            from sqlalchemy.exc import DBAPIError
            
            conn = ds['engine'].raw_connection()
            
            
            if ds['engine'].name != 'postgresql': 
                conn.connection.text_factory = str
                
            #print 'conn=',conn.connection
        
            
            data = ds['engine'].execute(query.limit(thelimit).offset(theoffset).apply_labels())
                
            result['header']=[]            
            
            for t in data._cursor_description():                
                try:
                    u = unicode(t[0])
                except:
                    u = unicode(t[0],'utf8')
                    
                result['header'].append(u)
                     
            
            
            result['resultset']=[]
            firstRowRead = False
            
            warnings.filterwarnings('error')
            for row in data:                
                r=[]
                for col in row:
                    if col is None:
                        u = None
                    else:                    
                        if col and isinstance(col, decimal.Decimal):
                            u = col
                        else:
                            try:
                                u = unicode(col)
                            except:
                                try:
                                    u = unicode(col,'utf8')
                                except:
                                    u = str(col)
                        
                    r.append(u)
                result['resultset'].append(r)   
            
                        
            s2 = self.getQuery(datasourceId,tables,joins,selectedColumns,filtre,isCount=True)        
            r= ds['engine'].execute(s2).first()
            totalCount= r[0]
                        
            result['count'] = totalCount
            result['error'] = None
            return result     
        except Exception as er:   
            #print 'er is',er         
            
            traceback.print_exc(file=sys.stdout) 
            e = sys.exc_info()[1]            
            result['header']=[]
            result['resultset']=[]
            result['count'] = 0
            result['error'] = repr(er)
            return result
        finally:
            #conn.close()
            warnings.filterwarnings('ignore')
    
    def forceCast(self,col,coltype):
        if coltype=='INT':
            return cast(col,sqlalchemy.types.INTEGER)
        elif coltype == 'DEC':
            return cast(col,sqlalchemy.types.DECIMAL)
        elif coltype == 'STR':
            return cast(col,sqlalchemy.types.VARCHAR)
        elif coltype == 'DATE':
            return func.date(col)
            return cast(col,sqlalchemy.types.DATE)
        elif coltype == 'DATETIME':
            return func.datetime(col)
            return cast(col,sqlalchemy.types.DATETIME)            
        elif coltype == 'TIME':
            return func.time(col)
            return cast(col,sqlalchemy.types.TIME)
        
        elif coltype == 'BOOL':
            return cast(col,sqlalchemy.types.BOOLEAN)
        else :
            return col
        
    def castIfNecessary(self,tableId,columnName,tablesTypes,col):
        if not tablesTypes:
            return col
        
        if not tablesTypes[tableId] :
            return col
        
        coltype = tablesTypes[tableId][columnName]
        if coltype:
            (typenatif,type) = coltype
            if typenatif == type:
                return col
            else:
                return self.forceCast(col, type)
                #cast
                
                
    def getQuery(self,datasourceId,tables,joins,selectedColumns,filtre,isCount=False): 
         
        ds  = self.getDatasource(datasourceId)
        
        aliases={}
        tableTypes={}
        for tableId in tables:        
            tableName = tables[tableId]['tableName']
            aliasName = tables[tableId]['tableAlias']
            tableTypes[tableId] = tables[tableId]['tableTypes']
            
            if aliasName:
                aliases[tableId] = ds['tablesModel'][tableName].alias(aliasName)
            else:
                aliases[tableId] = ds['tablesModel'][tableName]
                
             
            
        tableIdUsedInJoin = set()
        
        joinsList = []
        
        from copy import deepcopy
        
        for jorigin in joins:             
            j = deepcopy(jorigin)          
            firstTableId =  j.pop(0)
            tableIdUsedInJoin.add(firstTableId)
            join_ = aliases[firstTableId]
            
            while j:
                nextJoinType = j.pop(0)
                if nextJoinType=="outer join" :
                    isOuter = True
                else:
                    isOuter = False
                    
                nextTableId= j.pop(0)
                joinWithTable = aliases[nextTableId]
                tableIdUsedInJoin.add(nextTableId)
                
                tid = j.pop(0)
                joinLeftTable = aliases[tid]
                colName = j.pop(0)                
                joinLeftColumn = self.castIfNecessary(tid,colName,tableTypes,joinLeftTable.c[colName])
                
                tid = j.pop(0) 
                joinRightTable = aliases[tid]
                colName = j.pop(0)
                joinRightColumn = self.castIfNecessary(tid,colName,tableTypes,joinRightTable.c[colName])
                
                join_ = join_.join(joinWithTable,joinLeftColumn == joinRightColumn,isouter=isOuter)
            joinsList.append(join_)
        
        fromClause = []
        for n in aliases:
            if n not in tableIdUsedInJoin:
                fromClause.append(aliases[n])
        
        for j in joinsList:            
            fromClause.append(j)
        
        if len(selectedColumns)>0:
            sc=[]
            gp=[] #group by
            ob=[] #order by
            
            for c in selectedColumns:
                tid = c['tableId']
                colName = c['column']        
                if c['func']:                    
                    col_ = self.castIfNecessary(tid,colName,tableTypes,aliases[c['tableId']].c[c['column']])
                    col = Function(c['func'],col_) #Function                                       
                else:
                    col_ = self.castIfNecessary(tid,colName,tableTypes,aliases[c['tableId']].c[c['column']])
                    col = col_
                    
                if c['newname']: # attetion cette ligne depend du bloc de c['func'] !! ne pas bouger de place (a cause de la variable col)
                    col = col.label(c['newname'])
                else:
                    col = col.label("%s_%s"%(aliases[c['tableId']],colName)) #1.5.7
                    
                if c['group']:
                    gorder = c['group']                    
                    gp.append((gorder,col))
                
                if c['order']:
                    (ordre,typeordre) = c['order']
                    if not typeordre:
                        col2 = col
                    elif typeordre == 'DESC':
                        col2 = desc(col)
                    elif typeordre=='ASC':
                        col2 = asc(col)
                    else:
                        col2 = col
                                   
                    ob.append((ordre,col2))         
                            
                sc.append(col)
                        
            gp.sort() 
            gp = [x[1] for x in gp] 
                
            ob.sort()
            ob = [x[1] for x in ob]                  
        else:
            sc="*" 
            gp=[]        
            ob=[]
        
        if isCount:
            if sc!="*":
                s = select(sc,from_obj=fromClause,use_labels=True)
                if filtre:
                    ft = self.buildFilter(filtre,aliases)
                    s = s.where(ft)
                if gp:            
                    s = s.group_by(*gp) 
                
                if ob:
                    s = s.order_by(*ob)     
                query = select([func.count("*")],from_obj=s.alias('x'))
            else:
                s = select([func.count("*")],from_obj=fromClause)
                if filtre:
                    ft = self.buildFilter(filtre,aliases)
                    s = s.where(ft)
                if gp:            
                    s = s.group_by(*gp) 
                
                if ob:
                    s = s.order_by(*ob)
                   
                query = s
                
        else:            
            s =  select(sc,from_obj=fromClause)
            if filtre:
                ft = self.buildFilter(filtre,aliases,tableTypes)
                s = s.where(ft)
            if gp:            
                s = s.group_by(*gp) 
            
            if ob:
                s = s.order_by(*ob)
               
            query = s
        
           
        return query
    
    def getCsv(self,datasourceId,tables,joins,selectedColumns,filtre,filename): # TODO ajouter les order et group
        import dbexplorer.client.ucsv as csv
        ds  = self.getDatasource(datasourceId)
        with open(filename, 'wb') as outfile:        
            outcsv = csv.writer(outfile)
            query = self.getQuery(datasourceId, tables, joins, selectedColumns, filtre)
            
            records = ds['engine'].execute(query)
            outcsv.writerow(records.keys())
            for curr in records:
                newcurr=[]
                for field in curr:                    
                    if field is None:
                        field=''
                    newcurr.append(field)                    
                outcsv.writerow(newcurr)
            # or maybe use outcsv.writerows(records)
            outfile.flush()
            outfile.close()
            outfile = None
    
    def getquerystringOld(self,statement,bind = None):
        from sqlalchemy.sql import visitors
        from sqlalchemy.sql.expression import _BindParamClause

        def replace_bind(b):
            if isinstance(b, _BindParamClause):
                # for demonstration only !  This line does **not** 
                # apply proper escaping, which varies by backend !
                # Please replace with proper escaping/quoting !                
                
                if isinstance(b.value, basestring):
                    value = b.value.replace("'","''").encode("utf-8") 
                    return literal_column("'%s'" % value)
                else:
                    value = b.value
                    return literal_column("%s" % value)

        d3 = visitors.replacement_traverse(statement, {}, replace_bind)
        return str(d3)
    
    def getquerystring(self,statement, bind=None): 
        #print "statement is",statement       
        import sqlalchemy.orm
        if isinstance(statement, sqlalchemy.orm.Query):
            if bind is None:
                bind = statement.session.get_bind(
                        statement._mapper_zero_or_none()
                )
            statement = statement.statement
        elif bind is None:
            bind = statement.bind 
    
        dialect = bind.dialect
        compiler = statement._compiler(dialect)
        class LiteralCompiler(compiler.__class__):                    
            def visit_bindparam(
                    self, bindparam, within_columns_clause=False, 
                    literal_binds=False, **kwargs
            ):
                return super(LiteralCompiler, self).render_literal_bindparam(
                        bindparam, within_columns_clause=within_columns_clause,
                        literal_binds=literal_binds, **kwargs
                )
                
            def render_literal_value(self, value, type_):
                """Render the value of a bind parameter as a quoted literal.

                This is used for statement sections that do not accept bind paramters
                on the target driver/database.

                This should be implemented by subclasses using the quoting services
                of the DBAPI.

                """
                if isinstance(value, basestring):
                    
                    try:
                        val = value.decode("utf8")
                    except:
                        try:
                            val = value.decode("latin1")                    
                        except:
                            val = value
                    
                    val = val.replace("'", "''")
                    return u"'%s'" % val
                elif value is None:
                    return "NULL"
                elif isinstance(value, (float, int, long)):
                    return repr(value)
                elif isinstance(value, decimal.Decimal):
                    return str(value)
                elif isinstance(value, datetime.datetime):
                    return "TO_DATE('%s','YYYY-MM-DD HH24:MI:SS')" % value.strftime("%Y-%m-%d %H:%M:%S")

                else:
                    raise NotImplementedError(
                                "Don't know how to literal-quote value %r" % value)        
    
        compiler = LiteralCompiler(dialect, statement)
        return compiler.process(statement)
        
    def getSqliteList(self):        
        from dbexplorer.server.storage import Datasource        
        result = self.dbSession.query(Datasource.name,Datasource.database).filter_by(engine='sqlite').order_by(Datasource.name).all()        
        filenames = []
        datasourcenames = []
        
        for row in result:
            filenames.append(row.database)
            datasourcenames.append(row.name)
            
        return (filenames,datasourcenames)        
    
        
    def computeDataFramePhi2(self,dataf):
        try:
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
        except Exception :
            traceback.print_exc(file=sys.stdout) 
            from pandas import DataFrame
            return DataFrame()

    def get_phi2(self,df,index1,index2):
        if index1 == index2:
            N = np.count_nonzero(df[index1].unique())            
            #N = len([dfwithnan[index1].unique()])            
            #return N
            return 0
            #return -1
            
        
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
    
    def scatterplot_matrix(self,data, names, types, plt,**kwargs):
        """Plots a scatterplot matrix of subplots.  Each row of "data" is plotted
        against other rows, resulting in a nrows by nrows grid of subplots with the
        diagonal subplots labeled with "names".  Additional keyword arguments are
        passed on to matplotlib's "plot" command. Returns the matplotlib figure
        object containg the subplot grid."""
        numvars, numdata = data.shape
        import matplotlib.dates as mdates
        
        for i in range(len(names)):
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
                
                
                axes[i,j].plot(data[j], data[i], linestyle='none',marker='.', alpha=0.2)
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
    
    def heatmap(self,x, row_header, column_header, row_method,
            column_method, row_metric, column_metric,
            color_gradient, filename,pylab,mpl,matplotlib):
    

        def RedBlackSkyBlue():
            cdict = {'red':   ((0.0, 0.0, 0.0),
                               (0.5, 0.0, 0.1),
                               (1.0, 1.0, 1.0)),
            
                     'green': ((0.0, 0.0, 0.9),
                               (0.5, 0.1, 0.0),
                               (1.0, 0.0, 0.0)),
            
                     'blue':  ((0.0, 0.0, 1.0),
                               (0.5, 0.1, 0.0),
                               (1.0, 0.0, 0.0))
                    }
        
            my_cmap = matplotlib.colors.LinearSegmentedColormap('my_colormap',cdict,256)
            return my_cmap
        
        def RedBlackBlue():
            cdict = {'red':   ((0.0, 0.0, 0.0),
                               (0.5, 0.0, 0.1),
                               (1.0, 1.0, 1.0)),
        
                     'green': ((0.0, 0.0, 0.0),
                               (1.0, 0.0, 0.0)),
            
                     'blue':  ((0.0, 0.0, 1.0),
                               (0.5, 0.1, 0.0),
                               (1.0, 0.0, 0.0))
                    }
        
            my_cmap = matplotlib.colors.LinearSegmentedColormap('my_colormap',cdict,256)
            return my_cmap
        
        def RedBlackGreen():
            cdict = {'red':   ((0.0, 0.0, 0.0),
                               (0.5, 0.0, 0.1),
                               (1.0, 1.0, 1.0)),
            
                     'blue': ((0.0, 0.0, 0.0),
                               (1.0, 0.0, 0.0)),
            
                     'green':  ((0.0, 0.0, 1.0),
                               (0.5, 0.1, 0.0),
                               (1.0, 0.0, 0.0))
                    }
            
            my_cmap = matplotlib.colors.LinearSegmentedColormap('my_colormap',cdict,256)
            return my_cmap
        
        def YellowBlackBlue():
            cdict = {'red':   ((0.0, 0.0, 0.0),
                               (0.5, 0.0, 0.1),
                               (1.0, 1.0, 1.0)),
            
                     'green': ((0.0, 0.0, 0.8),
                               (0.5, 0.1, 0.0),
                               (1.0, 1.0, 1.0)),
            
                     'blue':  ((0.0, 0.0, 1.0),
                               (0.5, 0.1, 0.0),
                               (1.0, 0.0, 0.0))
                    }
            ### yellow is created by adding y = 1 to RedBlackSkyBlue green last tuple
            ### modulate between blue and cyan using the last y var in the first green tuple
            my_cmap = matplotlib.colors.LinearSegmentedColormap('my_colormap',cdict,256)
            return my_cmap        
        """
        This below code is based in large part on the protype methods:
        http://old.nabble.com/How-to-plot-heatmap-with-matplotlib--td32534593.html
        http://stackoverflow.com/questions/7664826/how-to-get-flat-clustering-corresponding-to-color-clusters-in-the-dendrogram-cre
    
        x is an m by n ndarray, m observations, n genes
        """
        
        ### Define the color gradient to use based on the provided name
        n = len(x[0]); m = len(x)
        if color_gradient == 'red_white_blue':
            cmap=pylab.cm.bwr
        if color_gradient == 'red_black_sky':
            cmap=RedBlackSkyBlue()
        if color_gradient == 'red_black_blue':
            cmap=RedBlackBlue()
        if color_gradient == 'red_black_green':
            cmap=RedBlackGreen()
        if color_gradient == 'yellow_black_blue':
            cmap=YellowBlackBlue()
        if color_gradient == 'seismic':
            cmap=pylab.cm.seismic
        if color_gradient == 'green_white_purple':
            cmap=pylab.cm.PiYG_r
        if color_gradient == 'coolwarm':
            cmap=pylab.cm.coolwarm
    
        ### Scale the max and min colors so that 0 is white/black
        vmin=x.min()
        vmax=x.max()
        vmax = max([vmax,abs(vmin)])
        vmin = vmax*-1
        norm = mpl.colors.Normalize(vmin/2, vmax/2) ### adjust the max and min to scale these colors
    
        ### Scale the Matplotlib window size
        default_window_hight = 8.5
        default_window_width = 12
        fig = pylab.figure(figsize=(default_window_width,default_window_hight)) ### could use m,n to scale here
        color_bar_w = 0.015 ### Sufficient size to show
            
        ## calculate positions for all elements
        # ax1, placement of dendrogram 1, on the left of the heatmap
        #if row_method != None: w1 = 
        [ax1_x, ax1_y, ax1_w, ax1_h] = [0.05,0.22,0.2,0.6]   ### The second value controls the position of the matrix relative to the bottom of the view
        width_between_ax1_axr = 0.004
        height_between_ax1_axc = 0.004 ### distance between the top color bar axis and the matrix
        
        # axr, placement of row side colorbar
        [axr_x, axr_y, axr_w, axr_h] = [0.31,0.1,color_bar_w,0.6] ### second to last controls the width of the side color bar - 0.015 when showing
        axr_x = ax1_x + ax1_w + width_between_ax1_axr
        axr_y = ax1_y; axr_h = ax1_h
        width_between_axr_axm = 0.004
    
        # axc, placement of column side colorbar
        [axc_x, axc_y, axc_w, axc_h] = [0.4,0.63,0.5,color_bar_w] ### last one controls the hight of the top color bar - 0.015 when showing
        axc_x = axr_x + axr_w + width_between_axr_axm
        axc_y = ax1_y + ax1_h + height_between_ax1_axc
        height_between_axc_ax2 = 0.004
    
        # axm, placement of heatmap for the data matrix
        [axm_x, axm_y, axm_w, axm_h] = [0.4,0.9,2.5,0.5]
        axm_x = axr_x + axr_w + width_between_axr_axm
        axm_y = ax1_y; axm_h = ax1_h
        axm_w = axc_w
    
        # ax2, placement of dendrogram 2, on the top of the heatmap
        [ax2_x, ax2_y, ax2_w, ax2_h] = [0.3,0.72,0.6,0.15] ### last one controls hight of the dendrogram
        ax2_x = axr_x + axr_w + width_between_axr_axm
        ax2_y = ax1_y + ax1_h + height_between_ax1_axc + axc_h + height_between_axc_ax2
        ax2_w = axc_w
    
        # axcb - placement of the color legend
        [axcb_x, axcb_y, axcb_w, axcb_h] = [0.07,0.88,0.18,0.09]
    
        # Compute and plot top dendrogram
        if column_method != None:
            start_time = time.time()
            d2 = dist.pdist(x.T)
            D2 = dist.squareform(d2)
            ax2 = fig.add_axes([ax2_x, ax2_y, ax2_w, ax2_h], frame_on=True)
            Y2 = sch.linkage(D2, method=column_method, metric=column_metric) ### array-clustering metric - 'average', 'single', 'centroid', 'complete'
            Z2 = sch.dendrogram(Y2)
            ind2 = sch.fcluster(Y2,0.7*max(Y2[:,2]),'distance') ### This is the default behavior of dendrogram
            ax2.set_xticks([]) ### Hides ticks
            ax2.set_yticks([])
            
            
            time_diff = str(round(time.time()-start_time,1))
            #print 'Column clustering completed in %s seconds' % time_diff
        else:
            ind2 = ['NA']*len(column_header) ### Used for exporting the flat cluster data
            
        # Compute and plot left dendrogram.
        if row_method != None:
            start_time = time.time()
            d1 = dist.pdist(x)
            D1 = dist.squareform(d1)  # full matrix
            ax1 = fig.add_axes([ax1_x, ax1_y, ax1_w, ax1_h], frame_on=True) # frame_on may be False
            Y1 = sch.linkage(D1, method=row_method, metric=row_metric) ### gene-clustering metric - 'average', 'single', 'centroid', 'complete'
            Z1 = sch.dendrogram(Y1, orientation='right')
            ind1 = sch.fcluster(Y1,0.7*max(Y1[:,2]),'distance') ### This is the default behavior of dendrogram
            ax1.set_xticks([]) ### Hides ticks
            ax1.set_yticks([])
            time_diff = str(round(time.time()-start_time,1))
            #print 'Row clustering completed in %s seconds' % time_diff
        else:
            ind1 = ['NA']*len(row_header) ### Used for exporting the flat cluster data
            
        # Plot distance matrix.
        axm = fig.add_axes([axm_x, axm_y, axm_w, axm_h])  # axes for the data matrix
        xt = x
        if column_method != None:
            idx2 = Z2['leaves'] ### apply the clustering for the array-dendrograms to the actual matrix data
            xt = xt[:,idx2]
            ind2 = ind2[:,idx2] ### reorder the flat cluster to match the order of the leaves the dendrogram
        if row_method != None:
            idx1 = Z1['leaves'] ### apply the clustering for the gene-dendrograms to the actual matrix data
            xt = xt[idx1,:]   # xt is transformed x
            ind1 = ind1[idx1,:] ### reorder the flat cluster to match the order of the leaves the dendrogram
        ### taken from http://stackoverflow.com/questions/2982929/plotting-results-of-hierarchical-clustering-ontop-of-a-matrix-of-data-in-python/3011894#3011894
        im = axm.matshow(xt, aspect='auto', origin='lower', cmap=cmap, norm=norm,picker=False) ### norm=norm added to scale coloring of expression with zero = white or black
        
        axm.set_xticks([i for i in xrange(0,len(row_header))]) ### Hides x-ticks
        axm.set_yticks([i for i in xrange(0,len(row_header))])
                   
        # Add text
        new_row_header=[]
        new_column_header=[]
        for i in range(x.shape[0]):
            if row_method != None:                
                new_row_header.append(row_header[idx1[i]])                
            else:                    
                new_row_header.append(row_header[i])
                
        for i in range(x.shape[1]):
            if column_method != None:                
                new_column_header.append(column_header[idx2[i]])
            else: ### When not clustering columns                
                new_column_header.append(column_header[i])
        
        axm.yaxis.tick_right()                  
        axm.set_yticklabels(new_row_header)
        
        axm.xaxis.tick_bottom()
        axm.set_xticklabels(new_column_header,rotation=270)  
        
        
                
        # Plot color legend
        axcb = fig.add_axes([axcb_x, axcb_y, axcb_w, axcb_h], frame_on=False)  # axes for colorbar
        cb = mpl.colorbar.ColorbarBase(axcb, cmap=cmap, norm=norm, orientation='horizontal')
    
        return pylab.gcf(),new_row_header,new_column_header

                         
