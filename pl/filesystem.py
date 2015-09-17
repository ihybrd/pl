""" filesystem.py

Author : huyongbin
Created on : Apr. 2014

filesystem module considers files and directories are objects rather than a 
string name. By creating objects, frequent operations on files and directories
become easier. There are two main classes here: phile and directory. They both
inherits from BaseFileSystem class, which is responsible for some features 
both work for files and folders, such as accessiblity, rename and so on.


phile class is file class, since 'file' is a name of type defaultly defined 
in python, so we don't want to mess them up. Use phile class to create a file
object will be simply like this:

>>> my_file = phile('/users/huyongbin/Documents/script/test.py'')

To get the size in kb of this file:

>>> size = my_file.size('k') # options: b, k, m, g, it returns a float number.

Or get the name and dir of this file object by doing:

>>> print my_file.dir
'/users/huyongbin/Documents/script'
...
>>> print my_file.name
'test.py'


directory class is used to create directory object. Creating a directory object
would be as simple as doing with a file object:

>>> my_dir_obj = directory('/users/huyongbin/Documents/scripts')

Directory object is iterable, so you can use 'for' keyword to go through its
content:

>>> for child in my_dir_obj:
...     print child

This also gives you an option to iterate current path or entire directory tree
by doing this:

>>> my_dir_obj.walk_stat = True # set true if we want to go through entire tree

Or if you don't want to keep the variable for the object.

>>> for child in directory('/users/huyongbin/Documents/script', do_walk=True):
...     print child

Please be aware of that the variable 'child' is a tuple, which contains a full
path and a filesystem object, the filesystem object could be an instance of 
phile or an instance of directory. This is the importance of using filesystem
module, it raraly gives back just a file in string, mostly we will recieve an
object. Lets try something a bit more complicated:

>>> my_dir_obj = directory('/users/huyongbin/Documents/script')
>>> my_dir_obj.walk_stat = True
>>> for child in my_dir_obj:
...     full_path, obj = child
...     if obj == None:
...         continue
...     if obj.type == TypeFile:
...         obj.rename('new_%s' % obj.name)
...

The above code iterates the entire directory tree, finds out files and adds
prefix for them.

Note: obj can be None, which means there are some issue with the path provided.
the obj wasn't successfully created.

You can add new dir to the folder by doing this:

>>> new_dir = my_dir_obj.mkdir('my_new_dir')

which returns you an directory object.

>>> print new_dir.name
'my_new_dir'

Also there is a shortcut for adding file(s) into the directory, if you still 
keep the first file object we made in the first examle, you can do this

>>> new_dir + my_file

It magically copies the my_file into the new_dir, also, my_file can be a string
or a list of my file or string, all belows are working:

# let's create another file object first
>>> my_file2 = phile('/users/huyongbin/Documents/script/test2.py'')

# then ...
>>> ret = new_dir + my_file.path # if string, it needs a valid full file path
>>> ret = new_dir + [my_file, my_file2]
# or ...
>>> ret = new_dir + [my_file, my_file2.path] # some are paths, some are objects.

'ret' will be a list of pasted file objects in the new folder, you can do 
whatever you want with them.

Also '-' will remove the file(s) from the directory object

>>> new_dir - [file1, file2 ..]

Also, the above operation can be replaced by just using obj.add(other) or 
obj.sub(other), they are same.

Please read/check API doc see the usage of other functions.
"""
import os
import datetime
import shutil
import stat
import platform
import hashlib

__author__ = "ihybrd@gmail.com"

class FSError(Exception):
    """The general filesystem error."""

class TypeFile: 
    """filesystem file type defination."""

class TypeDirectory: 
    """filesystem directory type defination."""

class _BaseFileSystem(object):
    """_BaseFileSytem class defines the most basic filesystem object, which 
    contains methods and properties that can be shared by file or directory. 
    This class should be inherited by a file class or a directory class, which 
    contains more methods or properties with explicit purpose.
    """
    _size_unit = {'b':0,'k':1,'m':2,'g':3}
    
    def __init__(self, in_path):
        """ Initializes the filesystem-based instances such as phile or 
        directory. The Initializer validates the input path in order to 
        internally get an correct abslute path, is_unc and the type of the 
        object.

        Args:
            in_path: file path or dir path
        """
        # get platform name
        self._platform = platform.system().lower()
        # validate path, get is_unc, type
        self._path, self._is_unc, self._type = self._validate(in_path,
                self._platform)
        # normalize path, remove the seperater in the end
        self._size = os.path.getsize(self._path)

    def __eq__(self, other):
        """ x == y calls this method.
        
        Considers objects are same if they have same value for path and
        type, Or even a string can be equal to an object if the string value
        is same to the path value of the object.

        Example:
        >>> fs1 = BaseFileSystem('/test/file.txt')
        >>> fs2 = BaseFileSystem('/test/file.txt')
        >>> fs3 = '/test/file.txt'
        >>> fs1 == fs2
        True
        >>> fs1 == fs3
        True

        Args:
            other: can be a BaseFileSystem object or a string. If the input
                is string, it must be a valid path
                (*NOTE: the input path must with backslash in windows OS, 
                haven't tested on other OS yet)
        Returns:
            True if eq False if not.
        """
        if isinstance(other, _BaseFileSystem):
            return (self._path == other.path and self.type == other.type)
        elif isinstance(other, str):
            if os.path.exists(other):
                return self._path == os.path.abspath(other)
            else:
                return False
        else:
            return False
    
    def __ne__(self, other):
        """x != y or x <> y calls this method.
        
        Returns True if neq, otherwise returns False.
        """
        return not self.__eq__(other)

    def __hash__(self):
        """Returns hash(path)"""
        return hash(self._path)

    def __repr__(self):
        return '%s("%s")' % (self.__class__.__name__, self._path)

    def size(self, unit = 'k'):
        """Returns the size of the instance.

        Args:
            unit: determine the unit of the return value, there are 4 options
                for that: b, k, m, g

        TODO: make sure it works with directory. (file is ok now)
        """
        return self._size / float(pow(1024, _BaseFileSystem._size_unit[unit]))

    @property
    def path(self):
        """Returns the full path of the instance."""
        return self._path

    @property
    def type(self):
        """ Returns the type of the instance, 

        Returns TypeFile if the instance is a file or TypeDirectory if the
        instance is a directory, if none of them returns None.
        """
        return self._type
        
    def is_unc(self):
        """Returns if current path follows UNC (Universal Naming Convention).
        UNC is path like '//server/folder/..'

        (NOTE: this method only for Windows platform)
        
        Returns:
            True if it is or False if it isn't. If OS is not Window, returns
            None.
        """
        return self._is_unc

    @classmethod
    def _validate(cls, path, current_platform):
        """ Validates the input path.

        Args:
            path: path needs to be validated
            current_platform: windows, mac, or linux

        Returns:
            (abspath, is_unc, path_type)
        """
        if not os.path.exists(path): # if the path exists
            raise FSError('path not exists : "%s"' % path)
        if current_platform == 'windows': # if it's unc path on windows 
            unc, tail = os.path.splitunc(path)
            is_unc = os.path.ismount(unc)
        else:
            is_unc = None
        if os.path.isfile(path): # file
            assert cls == phile, "Please use phile('%s')" % path
            path_type = TypeFile
        elif os.path.isdir(path): # dir
            assert cls == directory, "Please use directory('%s')" % path
            path_type = TypeDirectory
        else:
            path_type = None
        return (os.path.abspath(path), is_unc, path_type)

    def create_time(self):
        """Returns datetime object of creating time."""
        return datetime.datetime.fromtimestamp(os.stat(self._path).st_ctime)
    
    def modify_time(self):
        """Returns datetime object of last modifying time."""
        return datetime.datetime.fromtimestamp(os.stat(self._path).st_mtime)
    
    def access_time(self):
        """Returns datetime object of last accessing time."""
        return datetime.datetime.fromtimestamp(os.stat(self._path).st_atime)
        
    @property
    def name(self):
        """Returns the name of the instance.
        
        If the instance is file object, returns file name (with extension name)
        If the instance is direcotry object, returns the folder name
        """
        return os.path.basename(self._path)

    @property
    def dir(self):
        """Returns the direcory of the instance.

        If the instance is file object, then the dir would be the folder path
        contains that file. If the instance is directory object, the dir would
        be the parent directory that contains the current directory.
        """
        return os.path.dirname(self._path)

    @property
    def readability(self):
        """Returns True if the file is readable, return False if it isn't. """
        return os.access(self._path, os.R_OK)
    
    @readability.setter
    def readability(self, input):
        os.chmod(self._path, stat.S_IREAD)
    
    @property
    def writability(self):
        """Returns True if the file is writable, return False if it isn't. """
        return os.access(self._path, os.W_OK)
        
    @writability.setter
    def writability(self, input):
        os.chmod(self._path, stat.S_IWRITE)
    
    def rename(self, new_name):
        """ Renames the instance.

        Args:
            new_name: the new name of the instance
        """
        if not self.writability:
            raise FSError("current file is not writable, check the permission")
        if os.path.exists(os.path.join(os.path.dirname(self._path), new_name)):
            raise FSError("file exists cannot use same name.")
        new_name = os.path.join(os.path.dirname(self._path), new_name)
        os.rename(self._path, new_name)
        self._path = new_name


class phile(_BaseFileSystem):
    """phile class inherits from _BaseFileSytem, please check with 
    BaseFileSystem class for more information about the methods and properties
    that can be used.
    
    This class defines the base file object, can be inherited and expanded by 
    other file based classes as well.
    """
    def __init__(self, in_path = None):
        super(phile, self).__init__(in_path)
        self.__size_md5 = 4096

    def is_lnk(self):
        """Chechs if the current file is a .lnk file"""

    def copy(self, target_file):
        """Copy the current file object to the target.
        
        Args:
            target_file: the target full path of the file.
        """
        if os.path.exists(target_file):
            raise FSError('%s exists.' % target_file)
        shutil.copy2(self._path, target_file)

    @property
    def md5(self):
        """ Return file md5.

        The below code was downloaded from the internet, some part have been
        modified to make it work with filesystem.py module. For getting the 
        original info, please check with url below.

        http://www.cnblogs.com/mmix2009/p/3229679.html
        """
        myhash = hashlib.md5()
        f = file(self._path, 'rb')
        while True:
             b = f.read(self.__size_md5)
             if not b:
                 break
             myhash.update(b)
        f.close()
        return myhash.hexdigest()

    def move(self):
        pass
        
    def owner(self):
        """"""


class _Diff(object):
    """ _Diff stores the diff info between two directories.
    """
    def __init__(self):
        self.dirA = None
        self.dirB = None
        self.addition = []
        self.removal = []
        self.change = []
    

class directory(_BaseFileSystem):
    """directory class inherits from _BaseFileSytem, please check with 
    BaseFileSystem class for more information about the methods and properties
    that can be used.
    
    This class defines the directory object, can be inherited and expanded by 
    other directory based classes as well.
    """
    _walk_err_collection = []
    
    def __init__(self, in_path, do_walk = False):
        """Initializes the directory object.

        Args:
            in_path: the full path of the directory object.
            do_walk: If true the iterator will go through the entire directory
                tree, otherwise just iterates the current dir.
        """
        super(directory, self).__init__(in_path)
        self._content = os.listdir(self._path + os.sep)
        self._do_walk = do_walk
    
    def __iter__(self):
        """Yields the information from the current directory.

        The inistance of directory class can be enumerable, use `for` keyword
        to iterate the instance. There are 2 options for the return content, 
        one is _do_walk = True, which returns all the file and direcotry in
        the entire tree structure, similar with calling the os.walk() function
        but with objects; otherwise returns files and directories just in the 
        current instance's folder, simplar with calling the os.listdir() but 
        with objects.
        
        Yields: A tuple, which contains ($path, $object)
            $path : full path of a file or a directory
            $object: the instance of phile class or directory class, the obj 
                can be None if it gets unexpected exceptions.
        """
        if not self._content:
            raise FSError("No file has been found, please check the directory")
        if self._do_walk:
            for ch in self._walk():
                yield ch
        else:
            for ch in self._no_walk():
                yield ch
    
    def _walk(self):
        """Walks through the entire directory tree, returns info in tuple.
        
        Args:
            top_path: the top path being walked through. Basically it should
                be the current instance's path, object._path
        Returns:
            ($path, $object)
        """
        for w in os.walk(self._path):
            path, dirs, files = w
            if files:
                for full in [os.path.join(path, f) for f in files]:
                    obj = self._get_obj(full, phile)
                    yield (full, obj)
            if dirs:
                for full in [os.path.join(path, d) for d in dirs]:
                    obj = self._get_obj(full, directory)
                    yield (full, obj)

    def _no_walk(self):
        """Lists files and directoried in the current instance's folder.
        
        Returns:
            ($path, $object)
        """
        # directory._walk_err_collection = []
        for full in [self._path + os.sep + i for i in self._content]:
            if os.path.isfile(full):
                cls = phile
            elif os.path.isdir(full):
                cls = directory
            else:
                cls = None
            obj = self._get_obj(full, cls)
            yield (full, obj)
            
    def _get_obj(self, full, cls):
        """Returns (None, error_info) with error info if there is any 
        Exception during the object creationm, otherwise returns (obj, None).
        """
        try:
            return cls(full)
        except Exception, e:
            directory._walk_err_collection.append((full, e))
            return None

    def __add__(self, other):
        """Add other file(s) to the current directory. Update the self._content
        after adding them.
        Args:
            other: can be a single file name in string or a list of file names.
        Returns:
            a list of new file object (copied).
        """
        result, ret = self._validate_other(other)
        new_file_list = []
        if not result:
            raise FSError("Please check your input file - %s" % str(other))
        for o in ret:
            new_path = self._path + os.sep + os.path.basename(o)
            if os.path.abspath(new_path) != os.path.abspath(o):
                shutil.copy2(o, new_path)
                new_file_list.append(phile(new_path))
            else:
                pass # ignore same filename 
        self._update()
        return new_file_list

    def add(self, other):
        """Calls __add__(other)"""
        return self.__add__(other)
    
    def __sub__(self, other):
        """ Removes other file(s) from the current directory. Update the 
        self._content after removing them.

        Args:
            other: can be a single file name (or phile object) or a list of 
                file names (or phile objects).
        """
        result, ret = self._validate_other(other)
        if not result:
            raise FSError("Please check your input file - %s" % str(other))
        for r in ret:
            if os.path.basename(r) not in self._content:
                raise FSError("%s cannot be found in %s" % (r, self._path))
        for o in ret:
            os.remove(o)
        self._update()        
    
    def sub(self, other):
        """Calls __sub__(other)"""
        self.__sub__(other)

    def _validate_other(self, other):
        """Check the validation of the input file(s).
        
        Args:
            other: file(s) or file object(s)
        Returns:
            a tuple of ($check_result, $a_list_of_file_path), if check result
            is False, None path would be returned.
        """
        if type(other) == list:
            if not other:
                return False, None # no files in the list.
            ret = []
            for check_result, file_name in self._validate_file_list(other):
                if check_result:
                    ret.append(file_name)
                else:
                    return False, None
            return True, ret
        else:
            result, path = self._validate_single_file(other)
            return result, [path]
        
    def _validate_single_file(self, other):
        """Check if a single input is a valid file
        
        Args:
            other: input when + with other object
        Returns:
            True if it's valid file name or a phile object else False.
        """
        if type(other) == str:
            return os.path.isfile(other), other
        elif isinstance(other, phile):
            return os.path.isfile(other.path), other.path
        else:
            return False, None

    def _validate_file_list(self, other):
        for o in other:
            yield self._validate_single_file(o)
            
    def _update(self):
        """Refreshes the content info from the directory"""
        self._content = os.listdir(self._path)
        
    def _parent(self):
        return self._path + os.sep + os.pardir # return parent dir in string

    # uses _search()
    def count(self, kw = None, do_walk = False):
        """Counts the contents in the directory filered by kw
        
        Args:
            kw : result will be filtered by keyword
            do_walk : count entire tree if set to True, otherwise only iterates
                the current path.
        Returns:
            The number of matches
        """
        if not kw and not do_walk:
            return len(self._content)
        elif kw and not do_walk:
            return len([ch for ch in self._content if kw == ch])
        elif kw and do_walk:
            return len(self._search(kw, True, self._walk))

    def _search(self, kw, is_match_full_name, generator):
        """ Searches the content from the current directory.

        Args:
            kw: the keword.
            is_match_full_name : make mode, it true, finds the result that 
                exactly matches the kw, otherwise only see if the result 
                contains the kw.
            generator: _walk or _no_walk method in this class.

        Returns:
            a list of matched object.
        """
        ret = []
        for yie_path, yie_obj in generator.__call__():
            if not yie_obj:
                continue
            if is_match_full_name:
                if yie_obj.name == kw:
                    ret.append(yie_obj)
            else:
                if kw in yie_obj.name:
                    ret.append(yie_obj)
        return ret

    # uses _search()
    #TODO: add filter for sep file and dir.
    def search(self, kw, do_walk = False):
        """Searches file or directory with keyword in the name.

        Example:
        >>> # search 'a' from a dir, returns objects with 'a' in its path name.
        >>> my_dir = directory('/test')
        >>> my_dir.search('a', )
        [phile('/test/abc.txt'), directory('/test/a')]

        Args:
            kw: the keyword.
            do_walk : if go through the entire tree.
        Returns:
            a list of objects that matches condition.
        """
        if do_walk:
            generator = self._walk
        else:
            generator = self._no_walk
        return self._search(kw, False, generator)
    
    # uses _search()
    def has(self, kw):
        """ Find file or folder in the current directory. It's same to call
        search(kw = keyword, do_walk = False)

        Args:
            kw: the name
        Returns:
            a list of return object.
        """
        return self._search(kw, True, self._no_walk)
    
    def mkdir(self, in_name):
        """Creates a new folder in the current directory object.
        
        Args:
            in_name: the new folder name.
        Returns:
            The instance of new created folder.
        """
        new_dir = os.path.join(self._path, in_name)
        if in_name in self.content:
            return directory(new_dir)
        if not self.writability:
            raise FSError()
        os.mkdir(new_dir) # TODO: add check here to ensure dir creation's done.
        self._update()
        return directory(new_dir)

    def mkdirs(self, in_name):
        """Creates a new folder in the current directory object.
        
        Args:
            in_name: the new folder name.
        Returns:
            The instance of new created folder.
        """
        new_dir = os.path.join(self._path, in_name)
        os.makedirs(new_dir)
        self._update()
        return directory(new_dir)

    # this method should be improved to add code of protecting the dir and 
    # the instance. 
    # TODO: add codes for checking the authority of the dir; find a way to del
    #     the instance which wouldn't be existed anymore.
    def delete(self):
        """delele current dir (not finished) """
        shutil.rmtree(self._path)

    @property
    def parent(self):
        return directory(self._parent())
    
    @property
    def content(self):
        """Returns the contents (file, folder) in current path."""
        return self._content

    def ls(self):
        """Lists the content of the current directory object."""
        return self._content
        
    @property
    def walk_stat(self):
        return self._do_walk
        
    @walk_stat.setter
    def walk_stat(self, stat):
        self._do_walk = stat

    def is_empty(self):
        """Check if the directory is empty.
        Returns:
            True if it's empty, otherwise returns False.
        """
        if self._content:
            return False
        else:
            return True

    def copy(self, destination):
        """ Copy the current dir to destination.
        
        Args:
            destination: the target folder where current dir being copied to.
        Returns:
            target directory object, if gets error None would be returned by
            default.
        """
        if not os.path.isdir(destination):
            raise FSError()
        if not self.writability:
            raise FSError("current file is not writable, check the permission")
        current_dir_name = os.path.basename(self._path)        
        target_dir = os.path.abspath(destination) + os.sep + current_dir_name
        if current_dir_name not in os.listdir(destination):
            shutil.copytree(self._path, target_dir)
        else:
            raise FSError("folder exists, can not override it.")
        return directory(target_dir)

    def move(self, destination):
        shutil.move(self._path, destination)
        
    def _diff(self, A, B):
        """ This function only compares B with A, to find if all files in dir A
        exist in B. If some files in A are not in B, put them in diff.addition.
        If relative same file has different md5, put it in diff.change.
        
        Args:
            A: directory A
            B: directory B
        
        Returns:
            Diff object.
        """
        diff = _Diff()
        for path, obj in A._walk():
            if not obj or obj.type == TypeDirectory:
                continue
            B_f = B.path + obj.path.replace(A.path, "") # get the file path of B
            if os.path.exists(B_f): # check if B_f exists
                B_file_obj = phile(B_f)
                if B_file_obj.md5 != obj.md5: # check if md5 is same
                    diff.change.append(B_file_obj)
            else:
                diff.addition.append(obj)
        return diff
        
    def diff(self, other):
        """ Compares current directory object with another one and returns 
        _Diff object.
        
        In _Diff object, 
        diff.addition lists files that should be added to the another dir.
        diff.removal lists files that should be removed from the another dir.
        diff.change lists files that have been edited (with different md5)
        
        Args:
            other: the directory object to compare with.
            
        Returns:
            _Diff object
        """
        if type(other) == str:
            other_dir = directory(other)
        elif isinstance(other, directory):
            other_dir = other
        else:
            raise FSError("The type of parameter is not correct")
        diff = _Diff()
        diff.dirA = self
        diff.dirB = other_dir
        # compare dirs with each other.
        difA = self._diff(self, other_dir)
        difB = self._diff(other_dir, self)
        # what needs to be added to B is B addition list.
        diff.addition = difA.addition
        # what needs to be added to A is something that should be removed from B
        diff.removal = difB.addition
        # for each other, change should be same.
        diff.change = difA.change
        return diff
        
        
        
