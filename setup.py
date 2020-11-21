#!/usr/bin/python
# -*- coding: utf-8 -*-
# Python 2.6

 
import sys, os
from cx_Freeze import setup, Executable
 
#############################################################################
# préparation des options 
 
# chemins de recherche des modules
import os
#import pysideuic

import PySide

path = sys.path + ["dbexplorer"]

# options d'inclusion/exclusion des modules
includes = ["MySQLdb",'atexit','sqlalchemy','sqlalchemy.dialects.mysql','sqlalchemy.dialects.sqlite','numpy.lib.format']
excludes = []
packages = []
 
# copier les fichiers et/ou répertoires et leur contenu
#(os.path.join(os.path.dirname(pysideuic.__file__),"widget-plugins"), "pysideuic.widget-plugins")
includefiles = [(os.path.join(os.path.dirname(PySide.__file__),"plugins/imageformats"), "imageformats"),("resources","resources"),("img","img"),("locale-folder","locale-folder"),("static","static")] #[("aide", "aide")]

'''
if sys.platform == "linux2":
    includefiles += [(r"/usr/lib/qt4/plugins/sqldrivers","sqldrivers")]
elif sys.platform == "win32":
    includefiles += [(r"C:\Python27\Lib\site-packages\PyQt4\plugins\sqldrivers","sqldrivers")]
else:
    pass
''' 
# inclusion éventuelle de bibliothèques supplémentaires
binpathincludes = []
if sys.platform == "linux2":
    # pour que les bibliothèques de /usr/lib soient copiées aussi
    binpathincludes += ["/usr/lib","/usr/local/lib"]
elif sys.platform == "win32":
    binpathincludes += ["c:/python27/lib"]
 
# construction du dictionnaire des options
options = {"path": path,
           "includes": includes,
           "excludes": excludes,
           "packages": packages,
           "include_files": includefiles,
           "bin_path_includes": binpathincludes
           }
 
#############################################################################
# préparation des cibles
base = None
if sys.platform == "win32":
    base = "Win32GUI"
 
cible_1 = Executable(
    script = "dbexplorer.py",
    base = base,
    compress = True,
    icon = None,
    )
 
#############################################################################
# création du setup
setup(
    name = "dbexplorer",
    version = "1",
    description = "Explorateur de bases de données",
    author = "Laurent Frobert",
    options = {"build_exe": options},
    executables = [cible_1]
    )