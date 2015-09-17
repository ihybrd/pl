"""
This module is used for creating Maya UI. Instead of using the default
command provided by autodesk, this module provides much more readable way

author    - huyongbin
create on nov29 2012
"""

import maya.cmds as mc
import types


def __err_inst__(_class):
    raise ValueError("instance of class %s is needed" % (_class.__name__))

def __err_flag__(_flag):
    raise AttributeError("-%s is invalid flag" % (_flag))

def del_win(ui):
    if ui in mc.lsUI(wnd = True):
        mc.delete(ui)

def has_ui(ui):
    """Return if the ui exists in the current scene"""
    if ui in mc.lsUI(wnd = True):
        return True
    else:
        return False

def message(title = "Message", msg = ""):
    mc.confirmDialog(t = title, m = msg, b = ['ok'])

def confirm(title = "Confirm", msg = "Are you sure?"):
    """
    Launches a yes/no query window.

    Returns:
        True(yes) or False(no)
    """
    answer = mc.confirmDialog(title = title, m = msg, b = ['Yes', 'No'],
                                defaultButton = 'Yes', cancelButton = 'No',
                                dismissString = 'No')

    return False if answer == "No" else True

class MayaUiWrapperError(object):
    pass

class _WidgetPosition(object):
    """
    _WidgetPosition, the most basic layer of the wrapper, is used for storing
    the position infomation of a Maya UI element wrapped by UIWrapper, but
    these position information can only be used by FormLayoutWrapper. The
    FormLayoutWrapper object will recieve the a list of wrapped Maya UI 
    element with the position infomation, then build the final layout.
    
    Attribute:
    top         - called by __settop__
    bottom    - called by __setbottom__
    left        - called by __setleft__
    right     - called by __setright__
    _2t_        - called by fromTop
    _2b_        - called by fromBottm
    _2l_        - called by fromLeft
    _2r_        - called by fromRight
    _hasattach - if the object has be attached to another ui object
                    this value would be True.
    """
    def init_pos(self):
        self.__dict__['top'] = None
        self.__dict__['bottom'] = None
        self.__dict__['left'] = None
        self.__dict__['right'] = None
        
        self.__dict__['_2t_'] = None
        self.__dict__['_2b_'] = None
        self.__dict__['_2l_'] = None
        self.__dict__['_2r_'] = None

        self.__dict__['_hasattach'] = False
        
    def __settop__(self, dist):
        self.__dict__['top'] = (self._name, "top", dist)
    
    def __setbottom__(self, dist):
        self.__dict__['bottom'] = (self._name, "bottom", dist)
        
    def __setleft__(self, dist):
        self.__dict__['left'] = (self._name, "left", dist)
        
    def __setright__(self, dist):
        self.__dict__['right'] = (self._name, "right", dist)

    def topFrom(self, tar, dist):
        self.__dict__['_2t_'] = (self._name, "top", dist, tar._name)
        self.__dict__['_hasattach'] = True
    
    def bottomFrom(self, tar, dist):
        self.__dict__['_2b_'] = (self._name, "bottom", dist, tar._name)
        self.__dict__['_hasattach'] = True
    
    def leftFrom(self, tar, dist):
        self.__dict__['_2l_'] = (self._name, "left", dist, tar._name)
        self.__dict__['_hasattach'] = True
    
    def rightFrom(self, tar, dist):
        self.__dict__['_2r_'] = (self._name, "right", dist, tar._name)
        self.__dict__['_hasattach'] = True

    def setMargin(self, left = None, right = None, top = None, bottom = None):
        """
        Set the distance between the object edge and parent form edge.
        """
        if left != None:
            self.__setleft__(left)

        if right != None:
            self.__setright__(right)

        if top != None:
            self.__settop__(top)
            
        if bottom != None:
            self.__setbottom__(bottom)

    def setNeighbor(self, left = None, right = None, top = None, bottom = None):
        """
        Set the distance between the object edge and neighbor edge.
        """
        if left != None:
            self.leftFrom(left[0], left[1])

        if right != None:
            self.rightFrom(right[0], right[1])

        if top != None:
            self.topFrom(top[0], top[1])
            
        if bottom != None:
            self.bottomFrom(bottom[0], bottom[1])

    def getAttachForm(self):
        af = [self.top, self.bottom, self.left, self.right]
        return [o for o in af if o != None]
    
    def getAttachControl(self):
        ac = [self._2t_, self._2b_, self._2l_, self._2r_]
        return [o for o in ac if o != None]


class CommandHelp(object):
    """
    This class create an command help object which allows user to access the 
    help of a maya command easily in a proper data structure (not a huge str)

    __cmd__    - is the function object.
    flags        - all the flag names with both long name and short name, the 
                 the wrapper will check thi this list to see if the obj.att
                 is invalide or not.
    flag_type    - a dictionary with all the flag names and its spec type, the 
                 wrapper will check the type of the attribute. eg: if the att
                 is `c`, the __getattr__behavior would be differnt.
    """
    def __init__(self, cmd):
        self.__cmd__ = cmd
        self.flags = []
        self.flag_typ = {}
        self.__gethelp__()

    def __gethelp__(self):
        """
        the function will get the help string via the command of mc.help, then
        re-format the string into a list and add some valuable data to the 
        attribute flags and flag_type.
        """
        _dict = []

        for ln in mc.help(self.__cmd__.__name__).split("\n"):
            if str(ln).strip().startswith("-"):
                ent = []

                for i in ln.strip().split(" "):
                    if i:
                        ent.append(i)

                flags = [f[1:] for f in ent[:2]]
                sn, ln = flags

                self.flags += flags

                typ = None
                if len(ent) > 2:
                    typ = ent[2:]
                    typ = [str(t) for t in typ]

                entry = [flags, typ]
                self.flag_typ[str(sn)] = typ
                self.flag_typ[str(ln)] = typ

                _dict.append(entry)

        return _dict


class CommandAttribute(object):
    """ CommandAttribute will be instantiated if the UIWrapper recieves an 
    attribute which is a Script flag in maya command such as `c` or `ec`,
    """
    def __init__(self, att, parent):
        self.att = att
        self.parent = parent

    def __rshift__(self, other):
        """
        `>>` operator will recieve a list/tuple or a function. If it recieves 
        a function directly, the function would be just called. If it recieves
        a list or tuple, the first parameter of the list would be the be-called
        function, and the second parameter would be the argument, if the the 
        function need multiple arguments, a list is needed for the second 
        parameter.
        """
        if type(other) == types.FunctionType or\
             type(other) == types.LambdaType or\
             type(other) == types.MethodType:
            func = other
            self.parent._func.__call__(self.parent._name, e = 1,
                    **{self.att:func})
        else:
            func, parm = other
            # note for lambda: maya python ui command flag will pass a 
            # default args to any function you defined. so the func you
            # have define should have at least one arg.
            self.parent._func.__call__(self.parent._name, e = 1,
                    **{self.att:lambda arg = None, p = parm : func(arg, p)})


class UIWrapper(_WidgetPosition):
    """ UIWrapper wraps the maya.cmds UI command. 
    
    This class is intended to be used for creating a new style of way when
    creating maya UI. The common way of using 
    maya.cmds.command(obj, q = 1, att = 1) to query the value or using
    maya.cmds.command(obj, e = 1, att = val) to edit the value will be
    replaced by just say `wr_obj.att` to query and `wr_obj.att = val` to 
    edit. The wr_obj.att doesn't exists by default, because the wrapped cmd
    would probably have different flags, so the __getattr__ and __getattr__
    built-in method provides a dynamically way to achieve the access of 
    those flags via the way of typing `wr_obj.att`. Also if the wrapped object
    is a layout command, the close statement like `setParent` could be removed
    when you use `with` key, which saves number of lines of the code and bings
    up the good understanding of the indent.

    -func        - the passed maya function
    _name        - the name of the object
    _kw_ignore - the keyword that needs to be ingnored.
    help         - the help. see class CommandAttributes

    *getattr - all the gotten attribute which matches the function parameters.
    """
    def __init__(self, func, *args, **kwargs):
        """
        func     - the maya.cmds function being wrapped in this class.
        obj_name - is the the maya ui element is object name. Set it if needed.
        ext        - tells the wrap if the extended arg needed.
        **args     - used for those args that has to be define in __init__
        """
        # used for init pos of the ui widget
        self.init_pos()
        # NOTE: 
        # below init attr defination must be done like this:
        # >>> self.__dict__[attribute_name] = value
        # instead of doing like this :
        # >>> self.attribute_name = value 
        # >>> # this causes recursion depth exceed problem
        self.__dict__['_func'] = func
        self.__dict__['_name'] = func.__call__(*args, **kwargs)
        self.__dict__['_kw_ignore'] = ['left', 'right', 'top', 'bottom']
        self.__dict__['help'] = CommandHelp(func)

    def __getattr__(self, att):
        """ Get attribute with -q flag. This function allows user to get the 
        value of the maya ui argument via `cmds.ui.attr` instead of using
        `cmds.ui(q = 1, att = 1)`
        """
        if self.help.flag_typ[att] == ["Script"]:
            return CommandAttribute(att, self)
        if att in self.help.flags:
            return self.__cmd__(is_get = True, at = att)
        elif att in self._kw_ignore:
            return self.__dict__[att]
        else:
            __err_flag__(att)
            return None

    def __setattr__(self, att, val):
        """ Set attribute with -e flag. This function allows user to set a 
        value to the maya ui argument via `cmd.ui.attr = val` instead of using
        `cmd.ui(e = 1, att = val)`
        """
        if att in self.help.flags:
            self.__cmd__(at = att, v = val)
        elif att in self._kw_ignore:
            self.__dict__["__set%s__" % att].__call__(att, val)
        else:
            __err_flag__(att)
    
    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        """ When exiting the with statement, if the current object is window,
        uses showWindow to display the window, use setparent to up level to 
        close the layout. 
        """
        if self._func.__name__ == "window":
            mc.showWindow(self._name)
        else:
            mc.setParent(u = 1)

    def __gt__(self, form_parent):
        """ `>` calls this function, it parents the self object to the input
        form_parent object. `form_parent` object is the FormLayout object.
        Using __gt__ for the pareting could easily append the self object to
        the parent's widgets attribute.
        """
        self.__setattr__("p", form_parent._name)
        form_parent.widgets.append(self)

    def __cmd__(self, is_get = False, at = None, v = None):
        """return command string"""
        if is_get:
            return self._func.__call__(self._name, q = 1, **{at:1})
        else:
            return self._func.__call__(self._name, e = 1, **{at:v})


    def setAttributes(self, **args):
        """ get multi-parameter inputs. eg: object.set(width = 12, height = 11)
        """
        for att in args:
            self.__cmd__(at = att, v = args[att])
    

wr = UIWrapper


class FormLayoutWrapper(UIWrapper):
    """ This is the wrapper of the cmds.formLayout command.

    widgets    - is the build-ready list of ui elements
    """    
    def __enter__(self):
        self.__dict__["widgets"] = []
        return self
    
    def __exit__(self, type, value, traceback):
        self.__build__(self.widgets)

    def __build__(self, widgets):
        lsaf = []
        lsac = []
        for wgt in widgets:
            lsaf += wgt.getAttachForm()
            if wgt._hasattach:
                lsac += wgt.getAttachControl()

        self._func.__call__(self._name, e = True, af = lsaf, ac = lsac)
    
    def get_ui(self, widgets):
        self.widgets = widgets

wrf = FormLayoutWrapper


class ProgressWindowWrapper(object):
    """ ProgressWindowWrapper class allows Maya user to create a progress 
    object. it's' would be very easy to handle the code style, clear to push 
    progress to start, goto next and end. Here is an example, to show how the 
    class works in maya.

    with wrp(mc.progressWindows, content, title) as p:
        for i in p.content:
            if p.isbroken():
                doSomething()
                p.next()
    
    Attribute:
        __max__ - the max value of the progress
        __step__- the single jump value number
        func    - the function passed
        title     - the title of the progress window
        content - the list
    """
    def __init__(self, func, content, title, state, maximum = 100.0):
        self.func = func
        self.state = state
        self.title = title
        self.content = content

        self.__max__ = maximum
        self.__step__ = self.__max__/len(content)
        self.__reset__()

    def __enter__(self):
        self.func.__call__(t = self.title, pr = self.__value__, max = 100,
                             st = self.state, isInterruptable = True)

        return self

    def __exit__(self, type, val, trackback):
        self.func.__call__(ep = True)
        self.__reset__()
    
    def __reset__(self):
        self.__value__ = 0

    def isbroken(self):
        if self.func.__call__(q = True, isCancelled = True):
            self.__reset__()
            return True
        
        if self.func.__call__(q = True, pr = True) >= self.__max__:
            return True

        return False

    def next(self):
        self.__value__ += self.__step__
        self.func.__call__(e = True, pr = self.__value__)

wrp = ProgressWindowWrapper 


