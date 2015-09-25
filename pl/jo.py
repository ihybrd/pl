""" Json Object

Created on : Aug. 2014

# Example 1, simple json dict

>>> jobj = JsonObject('{"a":1, "b";2}')
>>> print jobj.a
1
>>> print jobj.b
2

# Example 2, nested dict in json string

>>> jobj = JsonObject('{"a":1,"b":{"c":3}}')
>>> print jobj.a
1
>>> print jobj.b
<json object>
>>> print jobj.b.c
3

# Example 3, let's start a jo from scratch!

>>> jobj = JsonObject() # empty {} by default. 
>>> jobj.to_json_string()
'{}'
>>> jobj.persons = {"A":{"name":"A", "age":1}, "B":{"name":"B","age":2}}
>>> 
"""

import json

__author__ = "ihybrd@gmail.com"

class JoError(Exception):
    """The general Json Object error."""

class JsonObject(object):
    """ JsonObject ( Jo ) wraps json string or python dictionary. It makes dict
    more like an object, allows you to access a dict via object attribute. It's
    actually working with object.__dict__. It also contains a lot of handy 
    function to make life easier.
    """
    def __init__(self, input_data = {}):
        """Constructor.

        Args:
            input_data: dictionroy or json string. An empty {} by default.
        """
        if type(input_data) == dict:
            self.__dict__ = input_data
        else:
            self.__dict__ = json.loads(input_data)
        self._analyse___dict__()
            
    def _analyse___dict__(self):
        """ Analyses the __dict__ if there is value with the type of dict, it 
        will be iterately creating JsonObject.
        """
        for key in self.__dict__:
            val = self.__dict__[key]
            if type(val) == dict:
                jo = JsonObject(val)
                self.__dict__[key] = jo
                
    def __add__(self, other):
        """ Merges with another Jo, a new Jo will be returned."""
        if not self._validate_type(other):
            raise JoError("JsonObject is required.")
        if not self._validate_keys_conflict(other):
            raise JoError("Keys conflict! 2 Jo has same key name.")
        new_dict = {} # init a new dict
        for k in self.ls():
            new_dict[k] = self.__dict__[k]
        for k in other.ls():
            new_dict[k] = other.__dict__[k]
        return JsonObject(new_dict)            

    def __repr__(self):
        return str(self.__dict__)
        
    def _validate_type(self, obj):
        """ Returns True if input obj is JsonObject, otherwise returns False.
        """
        if isinstance(obj, JsonObject):
            return True
        else:
            return False
            
    def _validate_keys_conflict(self, obj):
        """ Returns False if current Jo contains keys that input Jo has, 
        otherwise returns True.
        """
        ret = True
        for i in self.ls():
            if i in obj.ls():
                ret = False
                break
        return ret
    
    def ls(self):
        """ Returns the keys in current JsonObject (a list of string) """
        return self.__dict__.keys()
        
    def merge(self, jo):
        """ Merges with another Jo, a new Jo will be returned."""
        return self.__add__(jo)
        
    def add(self, key, val, dict_to_jo = True):
        """ Adds new attribute to the Json Object.

        Args:
            key: new key
            val: the value of new key.
            dict_to_jo: if true, dict type will be automatically converted to
                Jo format.
        """
        if self.__dict__.has_key(key):
            raise JoError("JsonObject already contains the key '%s'" % key)
        if dict_to_jo:
            if type(val) == dict:
                val = JsonObject(val)
        self.__dict__[key] = val
        
    def remove(self, key):
        """ Removes attribute from the current Json Object.
        
        Args:
            key : the name of the attribute
        """
        if not key in self.ls():
            raise JoError("key '%s' doesn't exist" % key)
        del self.__dict__[key]
    
    def update(self):
        """Self updates, refreshes the jo."""
        self._analyse___dict__()

    def _update(self, key, val, dict_to_jo = True):
        """ Updates the existed attribute's value.
        
        Args:
            key: the existed attribute's name
            val: the value of the existing attribute.
            dict_to_jo: if true, dict type will be automatically converted to
                    Jo format.        
        """
        if not key in self.ls():
            raise JoError("JsonObject doesn't contain the key '%s'" % key)
        if dict_to_jo:
            if type(val) == dict:
                val = JsonObject(val)
        self.__dict__[key] = val
        
    def has_key(self, key):
        """Returns True if current Jo has key otherwise returns False."""
        return key in self.ls()
        
    def to_json_string(self, convert_to_str = False):
        """Returns the json string by analysing object.__dict__
        
        Args:
            convert_to_str: True to convert return value to string, otherwise
                returns raw dict.
        """
        def _it_jo(jo):
            """iterates Jo to get dict info"""
            for k in jo.__dict__:
                val = jo.__dict__[k] # get value
                if isinstance(val, JsonObject): # if val is Jo
                    jo.__dict__[k] = _it_jo(val) # convert Jo to dict
            return jo.__dict__ # returns its dict anyway
        json_data = _it_jo(self)
        self.update()
        if convert_to_str:
            return str(json_data)
        else:
            return json_data
            
