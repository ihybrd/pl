""" interface.py

Interface is the way of asking people to follow conventions when working with
each other. Having this module can help you on restricting the interface 
conditions. You don't wanna have `<str> obj.name = 123` happened when objects
are being sent, since Python is quite dynamic, sometime it's really hard to 
controll. Also you might not like to have function like this:

>>> # This is a bad example of check input and output value.
>>> class Port(object):
...
...     def set_port(self, port_id):
...         if type(port_id) != int:
...             raise ValueError
...
...     def get_port(self):
...         if type(self._port_id) != int:
...             raise ValueError
...         else:
...             return self._port_id


That's why you are using this module - interface.py, This module gives very
easy way to define the rule, eg:


>>> # below is the way of defining an Interface class.
>>> class IPort(BaseInterface):
...
...     def set_port(self, port_id = int):
...         pass
...
...     @returns(int)
...     def get_port(self):
...         pass
...
>>> # so when you have the interface, you can use this rule anywhere
>>> # all the rules check were hidden behind
>>> class MyPort(IPort):
...
...     def set_port(self, port_id):
...         self._port_id  = port_id
...
...     def get_port(self):
...         return self._port_id
...
>>> # you can also put some attribute on the class
... class IPort(BaseInterface):
...
...     default = int
...     name = str
...
>>> class YourPort(IPort):
...
...     def __init__(self):
...         self.name = 'NOT_SET'
...
>>> uPort = YourPort()
>>> print uPort.name
'NOT_SET'
>>> # 'NOT_SET' is what you set as the name of your port
>>> print uPort.default
0
>>> # if default is not set, then returns a defualt type value
>>> # if you really wanna do something crazy
>>> uPort.name = 32123912301289310 # set INT to a STR var?? sorry..
# Error: ValueError: uPort.name is a string value, got int.
"""
import inspect
import types
import traceback
import os

__author__ = "huyongbin"

class InterfaceError(Exception):
    """Raise Interface Error"""
    def __init__(self, body):
        Exception.__init__(self, body)

    def _get_style(self, splitter = '.', duplicate = 20):
        """Returns the style of the error print."""
        return ">\n\n{0}\n%s\n{0}\n".format(splitter*duplicate)

    def get_body(self, *args):
        """Returns the body info with style."""
        return self._get_style() % '\n'.join(args)

    def get_err_loc(self):
        """Get the location of the error from a specific file.

        Returns:
            (filepath, linenumber) of the error
        """
        stack = traceback.extract_stack() 
        location = ''
        for idx in xrange(stack.__len__()):
            i = stack.__len__() - idx
            f_path, l_num, where, content = stack[i - 1] 
            f_crr = __file__
            if f_crr.endswith('.pyc'):
                f_crr = f_crr.replace('.pyc', '.py')
            # ignore errors that happening in __file__ (interface.py)
            if os.path.abspath(f_crr) != os.path.abspath(f_path):
                location = f_path, l_num
                return str(location)
        return None
    
    def get_func(self, f):
        """get the name of the function."""
        func = "%s.%s()" % (f.__bind_cls__, f.__name__)
        return func


class InterfaceValueError(InterfaceError):
    """Interface value error can be raised to nofity the value problem. It
    can be internally used only in the interface.py module. 

    >>> raise InterfaceValueError(f, required_info)
    ...
    Where : ('/path/file.py', 100)
    ErrorIn: func()
    Required: type<int>)
    "

    - Where tells where the issue is (filepath, linenumber)
    - ErrorIn tells what the func is (class.func())
    - Required tells what's expected.

    the func object must have a property 'f.__bind_cls__' which restores the 
    name of the bind class.
    """
    def __init__(self, func_obj = None, required = None):
        """
        Args:
            func_obj = function pointer
            required = information that is needed from user.
        """
        err_in = self.get_func(func_obj) if func_obj != None else ''
        body = self.get_body(
                "Where: %s" % self.get_err_loc(),
                "ErrorIn: %s" % err_in,
                "Required: %s" % required)
        InterfaceError.__init__(self, body)

class InterfaceInputValueError(InterfaceValueError):
    """Raises the error when capturing exception of input."""

class InterfaceOutputValueError(InterfaceValueError):
    """Raises the error when capturing exception of output."""


class _IValue(object):
    """This class wraps the input type"""

    def __init__(self, typ):
        """ Constructor.

        Args:
            typ: a type value
        """
        if type(typ) != type and type(typ) != _Interface:
            raise InterfaceValueError(required = "type value is required.")
        self.TYPE = typ
    
    def validate(self, f, input):
        """Validates the input value.

        Args:
            input: the input value from user
        """
        if type(input) != self.TYPE:
            f = None if not isinstance(f, types.FunctionType) else f
            raise InterfaceValueError(f, "%s is required" % str(self.TYPE)) 


# TODO: apply length of the list limitation.
class IList(_IValue):
    """IList represents a list of certain data type. eg:

    >>> class Port(object): pass
    >>> class IPortMgr(BaseInterface):
    ...     ports = IList(Port)
    ...
    >>> class PortMgr(IPortMgr): pass
    >>> portMgr = PortMgr()
    >>> portMgr.ports = [Port(), Port()] # this is ok
    >>> PortMgr.ports = [int(), Port()] # this would raise an error.

    It works same with the method attributes
    """

    def __init__(self, *typ):
        """Constructor.

        Args:
            typ: a type value
        """
        if typ.__len__() != 1:
            raise InterfaceValueError(
                    required = "one arg for list typ is required.")
        super(IList, self).__init__(*typ)

    def validate(self, f, input):
        """Validates the input value, checks if the input is a list and each 
        of its element is the pre-defined type.

        Args:
            input: the input value from user
        """
        if type(input) != list:
            raise InterfaceValueError(f, "type of list is required")
        for el in input:
            # call _IValue.validate()
            super(IList, self).validate(f, el)


class IOption(object):
    """IOption represents a date type that only allows using value in the 
    option list. eg:

    >>> class IPort(BaseInterface):
    ...    port_type = IOption('ftp', 'http')
    ...
    >>> class MyPort(IPort):
    ...    pass
    ...
    >>> port = MyPort()
    >>> port.port_type = 'abc'
    # Error : .. 'abc' not in ('ftp', 'http')
    ...
    >>> port.port_type = 'ftp'
    ...# OK

    Or you can define the data for the argument of the method. eg:

    >>> class IPort(BaseInterface):
    ...     def get_port_num(self, port_type = IOption('ftp', 'http')):
    ...         pass
    ...
    >>> port.get_port_num('ftp') # this is ok
    >>> port.get_port_num('abc') # this would raise an error.
    """

    def __init__(self, *args):
        """Constructor.

        Args:
            *args: suppose to be a list of values, and the required value of 
            the argument must be one of it.
        """
        if not args:
            raise InterfaceValueError(required = "IOption(*args)")
        self.OPTIONS = args

    def validate(self, f, input):
        """Validates the input value, checks if the input value in pre-defined
        options.

        Args:
            input: the input value from user
        """
        if input not in self.OPTIONS:
            rqr = "one of %s" % str(self.OPTIONS)
            f = None if not isinstance(f, types.FunctionType) else f
            raise InterfaceValueError(f, rqr)


_val = _IValue
ls = IList
opt = IOption
 

class _IFunction(object):
    """This class defines the data struct of the rule that would be applied 
    to the method of the class. This class will instantiated when IClass is 
    being created.

    A function interface contains 2 properties:

    - IN : rule for input
    - OUT : rule for output
    """
    def __init__(self, obj):
        """Constructor.

        Args:
            obj: the function object.
        """
        self.IN = self._get_args(obj)
        for idx, (arg, v) in enumerate(self.IN):
            # go through the arguements definition, if the rule is type, then
            # create value object, if they are ls or opt object, just leave it
            # otherwise, rasie an error.
            if type(v) == type:
                self.IN[idx] = arg, _IValue(v)
            elif type(v) != ls and type(v) != opt:
                raise InterfaceError("the function arguement must be type or "
                        "the instance of ls or opt.")
        self.OUT = obj.__returns__ if '__returns__' in dir(obj) else _IValue(type(None))
    
    def _get_args(self, f):
        """Returns the arguements information for the input function object.

        Args:
            f: function object.
        Returns:
            args info of a function
        """
        arg_names = inspect.getargspec(f).args[1:]
        arg_values = inspect.getargspec(f).defaults
        if arg_names:
            return zip(arg_names, arg_values)
        else:
            return []

# decorator
def returns(rtype):
    """This is the decorator of the method for defining the return value type
    in an Interface class.
    
    >>> # this is an example how to use the @returns on an interface method.

    >>> class IPort(BaseInterface):
    ...     @returns(int)
    ...     def get_port_num(self):
    ...         pass
    """
    def wrapper(f):
        if type(rtype) == type:
            f.__returns__ = _IValue(rtype)
        elif type(rtype) == ls or type(rtype) == opt:
            f.__returns__ = rtype
        else:
            raise InterfaceOutputValueError(
                    required = "return type def is wrong")
        return f
    return wrapper

# this is a very good example: https://www.python.org/dev/peps/pep-0318/
# for checking method input and output by using decorator.
def _check_method_IO(f):
    """Checkes the Input/Output rules of args and returns of the method. This
    function will be executed when initializing the class and its method, and 
    the wrapper below (new_f) will be created as well.

    NOTE: this decoration will be dynamically and internally used by the class.
    So no need to externally use @_check_method_IO to wrap the method again.
    
    Args:
        f: the decorated function.
    Returns:
        a new wrapped function.
    """
    def new_f(*args, **kwrd):
        """This function executed be when the relavant method is being called.

        * IMPORTANT *
        
        The attribute `__rule__` should have been attached on the function 
        before its being passed into the decorator. That's why the attribute 
        __rule__ can be accessible from the input function object.

        f.__rule__ is an instance of _IFunction class, which contains
        rules (input/output) of the function (f)
        """
        # use f.__rule to check input
        rules = [rule for a, rule in f.__rule__.IN]
        for rule, input in zip(rules, args[1:]):
            try:
                rule.validate(f, input)
            except InterfaceValueError:
                raise InterfaceInputValueError(required = "input error")

        # use f.__rule to check output
        result = f(*args, **kwrd)
        try:
            f.__rule__.OUT.validate(f, result)
        except InterfaceValueError:
            raise InterfaceOutputValueError(required = "output error")
        return result
    new_f.__doc__ = f.__doc__
    return new_f


class _IRule(object):
    """This class used for restoring rules for the interface."""

    def __init__(self):
        self.m = {}
        self.p = {}

    
# TODO: fix issue that _m and _p as cls attribute. this raise conflict when two
# class shares same function name or attr name!
# Solution can be using 
# _Interface.inst_cls = {cls1: {namespace}, cls2: {namespace}}
# each namespace contains {_m:... , _p:...}
class _Interface(type):
    """This is the metaclass for defining Interface.
    
    The class has 2 important class attributes:

    - cls.inst_cls : a dictionary of restoring instances of the metaclass, eg:
        { ClassA : IClassA_rule, ... }
    - cls.rules : a dictionary of restoring IClass rules, eg:
        { IClassA_rule : { m : method_rules, p : property_rules }, ... }
    """
    inst_cls = {} # instances of metaclass
    rules = {} # IClass rule info

    def __new__(mcls, name, bases, namespace):
        cls = super(_Interface, mcls).__new__(mcls, name, bases, namespace)
        if cls.__name__ == 'BaseInterface':
            return cls
        if [c for c in cls.__bases__ if c.__name__ == 'BaseInterface']:
            # judge if the current cls is IClass, if it is, the create rules
            cls._establish_rules(namespace)
        else:
            # bind rules with the relevant functions.
            cls._apply_rules_to_method(namespace)
        return cls
        
    def _establish_rules(cls, namespace):
        """This method will be called if the current class is judged as 
        the subclass of BaseInterface class, we can call it IClass, usually
        the naming convention of interface starts with 'I'. the IClass defines 
        the `rules` for its subclasses. Those rules will be appended to the
        cls._m for methods and cls._p for properties. The _m or _p are 
        dictionaries, the structure looks like this:

        cls._m = { method_name : <function-object>, ... }
        cls._p = { property_name : <IValue> | <IList> | <IOption> | ANY, ... }

        NOTE that a property can be one of 4 types mentioned above. 

        - IValue defines the interface as a type 
        - IList defines the interface as a list of type
        - IOption defines the interface as a value from the options
        - the ANY defines a fixed value for the property (read-only)

        Rules establishing would happen when IClass itself is being created.

        Args:
            cls: the current class
            namespace: containing the definitions for the class body.
        """
        if not cls.rules.has_key(cls.__name__):
            cls.rules[cls.__name__] = _IRule()
        for k, v in namespace.items():
            # get functions from current namespace dict
            if cls.rules[cls.__name__].m.has_key(k):
                continue
            if type(v) == types.FunctionType:
                # append function to the cls._m collection
                cls.rules[cls.__name__].m[k] = _IFunction(v)
            elif not k.startswith('__'):
                cls.rules[cls.__name__].p[k] = _IValue(v) if type(v) == type else v
                delattr(cls, k) # must del the rule setting info from cls

    def _apply_rules_to_method(cls, namespace):
        """Applies rules to the method.

        Rules applying would happen when the subclass of IClass 
        (the interface class) is being created. Two things would be executed
        during this process:

        - Checking method's arguement naming convention 
        - attach a decorator(_check_method_IO()) to each method.

        Args:
            cls: the current class
            namespace: containing the definitions for the class body.
        """
        base, = cls.__bases__ # get rule name
        if not cls.inst_cls.has_key(cls.__name__):
            cls.inst_cls[cls.__name__] = cls.rules[base.__name__]
        # if no rule for __init__ then override the one in base interface.
        if '__init__' not in cls.inst_cls[cls.__name__].m:
            def __init__(obj): pass
            setattr(cls, '__init__', __init__)
        for k in cls.inst_cls[cls.__name__].m.keys():
            # check missing functions.
            if k not in namespace.keys(): 
                raise InterfaceValueError(
                        required = "MISSING: %s() is not defined." % k)
            if type(namespace[k]) != types.FunctionType:
                continue
            # check arguement naming conventions.
            current_IN = inspect.getargspec(namespace[k]).args[1:] # 
            valid_IN = [arg for arg, val in cls.inst_cls[cls.__name__].m[k].IN]
            if valid_IN != current_IN:
                a = ','.join(valid_IN)
                raise InterfaceValueError(required = "the valid args for %s() "
                        "should be %s(%s)" % (k, k, a))
            # attach rule to the function, then wrap it (decorating)
            namespace[k].__rule__ = cls.inst_cls[cls.__name__].m[k] 
            namespace[k].__bind_cls__ = cls.__name__
            setattr(cls, k, _check_method_IO(namespace[k]))

            
class BaseInterface(object):
    """The BaseInterface needs to be inherited by IClass(-es), it can't be
    instantiated directly.

    BaseInterface also defines __setattr__() and __getattr__() to compare 
    the inputs with the cls._p, rules for properties, and raise Error if 
    there is any issue. Here is an example of using BaseInterface class.

    >>> # User BaseInterface to create IClass and define rules
    ...
    ... class IString(BaseInterface):
    ...
    ...     @returns(int)
    ...     def str_to_int(self, in_string = str):
    ...         pass
    ...
    >>> # Way of creating actually class by using the interface IString.
    ...
    ... class String(IString):
    ...
    ...     def str_to_int(self, in_string):
    ...         return int(in_string)

    In this case the method str_to_int in String class must have a str input
    and an integer return, and an Error would raised if the value type is
    not correct.
    """
    
    __metaclass__ = _Interface
    
    def __init__(self):
        """Constructor, BaseInterface shouldn't be instantiated."""
        raise InterfaceError("BaseInterface cannot be instantiated, it can "
            "only be interited by other class.")

    def __setattr__(self, name, value):
        """Overrides object method. When value assigning's happening like: 

        >>> obj.attr = val

        Args:
            name: the name of the attribute.
            value: the value of the attribute.
        """
        cls_name = self.__class__.__name__
        if not _Interface.inst_cls[cls_name].p.has_key(name):
            self.__dict__[name] = value
            return
        if type(_Interface.inst_cls[cls_name].p[name]) in [_val, ls, opt]:
            _Interface.inst_cls[cls_name].p[name].validate(name, value)
        else:
            raise InterfaceValueError(
                    required = "'%s' is read-only attribute" % name)
        self.__dict__[name] = value

    def __getattr__(self, name):
        """Returns the value of the attribute. 
        
        Check if the attr is exist in __dict__, return the value of it if it
        exists. if __dict__ doesn't find the key, then check the rules
        from _Interface._p, returns value if its defines, otherwise returns
        the default instance of that type. eg:

        if obj.age needs to be an integer, and obj.age hasn't defined, then
        the return value of obj.age would be int() -> 0. Same with str, if 
        obj.name needs to be a name, then str() -> '', an empty str would be 
        returned if it's not defined.

        Args:
            name: the name of the attribute.
        Returns:
            the value of the attribute, raise ValueError if attr not found.
        """
        if self.__dict__.has_key(name):
            return self.__dict__[name]
        cls_name = self.__class__.__name__
        # if no name available in __dict__, check if the key was in the rule.
        if _Interface.inst_cls[cls_name].p.has_key(name):
            if type(_Interface.inst_cls[cls_name].p[name]) in [ls, opt]:
                raise InterfaceValueError(
                        required = "attribute '%s' is not available" % name)
            elif type(_Interface.inst_cls[cls_name].p[name]) == _val:
                self.__dict__[name] = _Interface.inst_cls[cls_name].p[name].TYPE()
            else:
                self.__dict__[name] = _Interface.inst_cls[cls_name].p[name]
            return self.__dict__[name]
        else:
            raise InterfaceValueError(
                    required = "attribute '%s' is not available" % name)


