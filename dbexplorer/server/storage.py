# -*- coding: utf-8 -*-
"""
.. module:: storage
   :synopsis: classe d'accès aux données stockées
.. codeauthor:: pireh, amérique du nord, laurent frobert
"""
from sqlalchemy import *
from sqlalchemy.orm import relationship
from sqlalchemy.engine import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import *
from sqlalchemy.dialects.sqlite import DECIMAL
Base = declarative_base()

class Datasource(Base):
    __tablename__ = 'datasource'
    id = Column(Integer, primary_key=True)  
    engine = Column(String(),nullable = True)  
    name =  Column(String())
    username =  Column(String(),nullable = True)
    password =  Column(String(),nullable = True)
    host =  Column(String(),nullable = True)
    port =  Column(Integer(),nullable = True)
    database =  Column(String(),nullable = True)
    query = Column(String(),nullable = True)
    document =  Column(String(), nullable=True)
    
class Exploration(Base):
    __tablename__ = 'exploration'
    id = Column(Integer(), primary_key=True) #,autoincrement=False
    id_datasource = Column( Integer(), ForeignKey("datasource.id"), nullable=False)
    name =  Column(String(), nullable=False)  
    document =  Column(String(), nullable=True)
    

    
    
    
datasource = Datasource.__table__

exploration = Exploration.__table__

import os
def initStorageIfNecessary(fulldbpath):
    if not os.path.exists(fulldbpath) :
        try :            
            initStorage(fulldbpath)
        except Exception as error:
            print 'error initStorageIfNecessary',error
    else:
        #dbexplorer storage exist but is there the 'document field in exploration table '? (old version before 1.0)
        dbengine = create_engine('sqlite:///'+fulldbpath)
        try:
                        
            s = dbengine.execute("select document from exploration")
            s.close()
        except Exception as error:
            #no document column so alter exploration db
            dbengine.execute("alter table exploration add column document VARCHAR")
            
        try: # ajout colonne document contenant les nom des tables et leurs types natif et nouveau type
                        
            s = dbengine.execute("select document from datasource")
            s.close()
        except Exception as error:
            #no document column so alter exploration db
            dbengine.execute("alter table datasource add column document VARCHAR")
        
            
def initStorage(dbAbsolutePath):
    #table creation
    dbengine = create_engine('sqlite:///'+dbAbsolutePath)
    Base.metadata.create_all(dbengine) 

def insertSomeData():
    pass
    
    
    