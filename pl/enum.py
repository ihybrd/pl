import inspect

class EnumInitError(Exception):
    """Exception raised when instantiating Enum."""

class Enum(object):
    """ Pythonic enum type. With the constructor and the class namespace
    __dict__, the pythonic enum can be simply used like this:
    (NOTE: you have to specify the type at first input argument)
    
    >>> Direction = Enum(int, Left, Right, Up, Down)
    >>> print Direction.Left
    0
    >>> print Direction.Down
    3
    >>> Direction = Enum(str, Left, Right, Up, Down)
    >>> print Direction.Left
    'Left'
    """
    
    def __init__(self, type, *args):
        """Constructor.
        
        Args:
            type: str or int.
            *args: list of classes.
        """
        self._enum = []
        if type != str and type != int:
            raise EnumInitError("1st arg of __init__ must be 'int' or 'str'")
        for id, cls in enumerate(args):
            if not inspect.isclass(cls):
                raise EnumInitError("Invalid arg: %s is not a class" % str(cls))
            if type == str:
                self.__dict__[cls.__name__] = cls.__name__
            elif type == int:
                self.__dict__[cls.__name__] = id
            self._enum.append(cls.__name__)
                
    def ls(self):
        """Returns list of enumerators."""
        return self._enum
