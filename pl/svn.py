"""
Author: huyongbin
Created on: Jan 2015

This is the svn command line wrapper. In this module, Command class is the
most basic and generic command wrapper, other classes inherite from Commmand
with more specific feature and easier API access, but if you want more freedom
of using pythonic snv command, better use Command()._exec() which can almost
handle all the svn commmand features.

For the command wrapper, we call it Lazy API! For the lazy api, only common 
used API would be provided, if you need more flexible control of the args,
better to use Command()._exec().
"""
import subprocess
import utils
import os
import xml.etree.ElementTree as ElementTree

__author__ = "huyongbin@virtuosgames.com"

class svn: pass
class svnadmin: pass
class svnserve: pass

commands = utils.Enum(str, svn, svnadmin, svnserve)


class XmlTag(object):
    """ XmlTag class wraps the svn info in xml structure, allows user to access 
    the data in this way: log.revision, log.msg, etc. 
    """
    def __init__(self, xml_etree):
        """Constructor.
        
        Args:
            xml_etree: the log entry xml etree element.
        """
        self.__dict__ = xml_etree.attrib
        self._xml_etree = xml_etree
        for prop in xml_etree.find('.'):
            if '-' in prop.tag:
                tag = prop.tag.replace('-', '_')
            else:
                tag = prop.tag
            if self.__dict__.has_key(tag) and type(self.__dict__[tag]) == list:
                self.__dict__[tag].append(XmlTag(prop))
            elif self.__dict__.has_key(tag) and type(self.__dict__[tag]) != list:
                self.__dict__[tag] = [self.__dict__[tag], XmlTag(prop)]
            else:
                self.__dict__[tag] = XmlTag(prop)
    
    def __repr__(self):
        return self._xml_etree.text


class Command(object):
    """General SVN command class. This class can be inherited by other classes
    or be used directly. By using _exec() directly, full access can be applied
    while the wrapper of the class provides limited but easy API.
    """

    def call(self, command, has_ret, **kwargs):
        """Svn command executer. 

        The first arg command needs to be <Enum> command type, which represents
        the main SVN command, and the rest of args must follow these rules:

        for subcommand, the arg should be a simple word. eg: create = $pth
        other arguments should startwith '_' or '__'. eg: (_d = 1, _r = $pth)
        any '-' in the command can be '_'. eg: (__fs_type = $val)

        Example 0:
        >>> cmd = Command() # create command object.

        Example 1:
        >>> cmd._exec(commands.svnserve, _d = 1, _r = $server_root_path)
        same with: svnserve -d -r $server_root_path

        Example 2:
        >>> cmd._exec(commands.svn, checkout = $path, __username = $name, 
                        __password = $password)
        same with: svn checkout $path --username $name --password $password
        
        Args:
            command: <util.Enum> the selected svn command. The command can be:
                svn, svnadmin, svnserve
            **kwargs: a dictionary contains some arguements.
        
        Returns:
            list of Revision objects.
        """
        self._exec(command, has_ret, **kwargs)

    def _exec(self, command, has_ret, **kwargs):
        args = [command.lower()]
        for key in kwargs.keys():
            val = kwargs[key]
            key = key.replace('_', '-') # replace _ with -
            if type(val) == bool or val in [0,1]:
                if val:
                    args.append(key)
            elif val == None:
                # key will be ignored as well, not gonna be available in the 
                # list of args. Reason to have it to make the args easiliy to 
                # be switched on or off when wrapping the command.
                continue
            else:
                if type(val) == list:
                    args += [key] + val
                else:
                    args += [key, val] if val else [key]

        if has_ret:
            p = subprocess.Popen(args, stdout = subprocess.PIPE)
            r = p.stdout.read()
            print r
            if '--xml' in args:
                # if --xml was appliedm, xml etree object would be returned.
                return ElementTree.fromstring(r)
            else:
                return r
        else:
            p = subprocess.Popen(args)
            p.communicate() # wait until the process finished.


class Client(Command):
    """Lazy API for command svn.exe"""

    def __init__(self):
        self._cmd = commands.svn

    def update(self, path, rev):
        """svn update subcommand.

        Args:
            path: local path.
            rev: the revision nunmber the path would be updated to.
        """
        if type(rev) != int:
            raise Exception('rev should be int')
        else:
            rev = str(rev)

        self._exec(self._cmd, False, update = path, _r = rev)

    def checkout(self, server, local):
        """Svn checkout command.
        
        Args:
            server: the server url
            local: the local path
        """
        self._exec(self._cmd, False, checkout = [server, local], 
                __username = 'anonymous', __password = 'anonymous')

    def add(self, paths):
        """Svn add command.
        
        Args:
            paths: files need to be added
        """
        paths = self._validate_path(paths)
        self._exec(self._cmd, False, add = paths) 

    def delete(self, paths):
        """Svn delete command.
        
        Args:
            paths: files need to be deleted.
        """
        paths = self._validate_path(paths)
        self._exec(self._cmd, False, delete = paths) 

    def commit(self, paths, message):
        """Svn commit command.
        
        Args:
            paths: files need to be commited
            message: commit message
        """
        paths = self._validate_path(paths)
        self._exec(self._cmd, False, commit = paths, _m = '"%s"' % message)

    def status(self, *paths):
        """Svn status command.
        
        Args:
            path: the local path

        Returns:
            <list of XmlTag object> the status of files under the path
        """
        paths = [os.path.abspath(path) for path in paths]
        # path = os.path.abspath(path)
        r = self._exec(self._cmd, True, status = paths, __xml = True)
        return [XmlTag(entry) for entry in r.find('.')]
    
    # TODO: have lock function
    def lock(self):
        pass

    def log(self, path, rev = None): 
        """svn log subcommand.
        
        Args:
            path: the repository path, can be started with http:// or svn://
            rev: there are 3 situation for rev
                1> None, show all the log for the path
                2> int, show the specific revision of the path
                3> [int, int], show range of revisions of the path

        Returns:
            list of revision object with log info
        """
        if type(rev) == int:
            rev = str(rev)
        elif type(rev) in (tuple, list) and len(rev) == 2 and\
                len([r for r in rev if type(r) == int]) == 2:
            # if rev is list, elements must be int, and the len must be 2
            # if correct, transfer [int, int] to "int:int" which's gonna be
            # used to represent range of commits
            rev = '%i:%i' % (rev[0], rev[1])
        elif rev != None:
            raise Exception('rev must be an int or list with 2 int')

        r = self._exec(self._cmd, True, log = path, _v = 1, __xml = 1, 
                _r = rev)

        return [XmlTag(logentry) for logentry in r.find('.')]

    # TODO: add path checker function inside.
    def _validate_path(self, paths):
        return [os.path.abspath(p) for p in paths]


class Admin(Command):
    """The lazy API for command svnadmin.exe"""

    def __init__(self):
        self._cmd = commands.svnadmin

    def create(self, repo):
        """Create repository.

        Args:
            repo: the path of the repository.
        """
        self._exec(self._cmd, False, create = repo)


class Serve(Command):
    """Lazy API for command svnserve.exe"""

    def __init__(self):
        self._cmd = commands.svnserve

    def run(self, root):
        """Call svnserve.exe to run the svn service.

        Args:
            root: the server root path
        """
        self._exec(self._cmd, False, _d = 1, _r = root)
