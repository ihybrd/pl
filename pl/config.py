"""Config.py

Created on : Sep 2015
Author: Hu Yongbin

This module simply wrappes ConfigParser module from original Python, so you
can access configure file in a pretty handy way.

Assume you have a configure file called example.ini like this:
(below INI example comes from https://en.wikipedia.org/wiki/INI_file)

---------------EXAMPLE-INI--------------
[owner]
name=John Doe
organization=Acme Widgets Inc.
 
[database]
server=192.0.2.62     
port=143
file=payroll.dat
----------------------------------------

By using config.py module, you can access it in this way, example:

# import the module first
>>> import config

# init the ini object
>>> conf = config.Config("example.ini")

# use pattern $obj.$section.$item
>>> print conf.owner.name
'John Doe'
>>> print conf.database.server
'192.0.2.62'

# you can print a section in dictionary
>>> print conf.owner.dict()
{'name':'John Doe', 'organization':'Acme Widgets Inc.'}

# or print entire ini in dictionary
>>> print conf.dict()
{'owner': {'name':'John Doe', 'organization':'Acme Widgets Inc.'}, 
'database': {'server':'192.0.2.62', 'port':'143', 'file':'payroll.dat'}}
"""
import ConfigParser


class Section(object):
    
    def __init__(self, conf, name):
        self.__conf = conf
        self.__name = name
        
    def __getattr__(self, attr):
        return self.__conf.get(self.__name, attr)
        
    def ls(self):
        """Returns a list of keys from the selected Section."""
        return self.__conf.options(self.__name)

    def val(self):
        """Returns a list of values from the selected Section."""
        return [self.__conf.get(self.__name, key) for key in self.ls()]

    def dict(self):
        """Returns section in dictionary."""
        r = {}
        for key in self.ls():
            r[key] = self.__conf.get(self.__name, key)
        return r


class Config(object):

    def __init__(self, path):
        self.__conf = ConfigParser.ConfigParser()
        self.__conf.read(path)
        
    def __getattr__(self, attr):
        return Section(self.__conf, attr)
    
    def ls(self):
        """Returns list of the section list."""
        return self.__conf.sections()
        
    def dict(self):
        """Returns config file in dictionary."""
        r = {}
        for section in self.ls():
            r[section] = Section(self.__conf, section).dict()
        return r