# -*- coding: utf-8 -*-
"""
.. module:: i18n
   :synopsis: Module pour la gestion des traductions des textes
.. codeauthor:: pireh, amérique du nord, laurent frobert
"""

import locale
import gettext,os
application = 'dbexplorer'
win_local_path = os.path.abspath('./locale-folder')
currentLang = None




def saveLang(lang,configpath):
    try :        
        f = open(os.path.join(configpath,'currentlang'), 'w')
        f.write(lang)                                                            
        f.close()  
    except:
        pass
    
    
def readfromconfig(configpath):
    try :        
        f = open(os.path.join(configpath,'currentlang'), 'r')                
        lang = f.read()                                                            
        f.close()  
    except:
        lang = locale.getdefaultlocale()[0][:2]
        if lang not in [u'fr',u'en']:
            lang=u'en'
    
    return lang

    
def getAvailableLangue():
    return [(u'fr',u'Français'),(u'en',u'English')]

def setCurrentLang(lang):
    try:    
        cur_lang = gettext.translation(application, localedir=win_local_path, languages=[lang])
        
        cur_lang.install(unicode=True) 
        global currentLang 
        currentLang = lang   
    except IOError:
        print 'error'    
        _ = lambda text:text
        
        
        