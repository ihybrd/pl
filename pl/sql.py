""" sql.py

Author : huyongbin
Created on : Nov. 2014

sql.py module helps python developer on generating SQL statement in a pythonic
way. So assuming you have a sql object, you can do something like this:

>>> sql.select(PLAYER.name, User.age > 10)

which does something same with SQL:

... select name from player where age > 10

Above line is a string that you are going to get when the function's called. 
Then you can put it into MySQLdb's cursor.execute($sql).

Belows are some more examples of using the class

>>> import sql as _sql
...
>>> # Init the class
>>> Table = _sql.Table
>>> SQL = _sql.SQL
...
>>> # Create table object
>>> User = Table('User')
...
>>> # Create SQL(db) object
>>> sql = SQL()
...
>>> # print some sql statement
>>> sql.select(User)
... SELECT * FROM User
...
>>> sql.select(User.name, User.age > 30)
... SELECT name FROM User WHERE age > 30
...
>>> sql.select(User.name, (User.age > 50, User.age < 30), User.gender == 'male')
... SELECT name FROM User WHERE (gender='male' AND (age > 50 OR age < 30))
...
>>> sql.insert(User, age = 30, name = 'YourName')
... INSERT INTO User (age,name) VALUES (30,'YourName')
...
>>> sql.update(User, User.age > 30, User.country == 'china', name='YourName', job = "TA")
... UPDATE User SET job='TA',name='YourName' WHERE ((age > 30 AND country='china'))
"""

class Column(object):
    """ Column object can compare with others """

    def __init__(self, name, table):
        self._name = name
        self._path_arr = [table, name]

    def __lt__(self, other):
        return self._name + "<" + str(other)

    def __gt__(self, other):
        return self._name + ">" + str(other)

    def __eq__(self, other):
        if type(other) == str:
            other = "'%s'" % other
        return self._name + "=" + str(other)

    def __ne__(self, other):
        return self._name + "<>" + str(other)

    def __le__(self, other):
        return self._name + "<=" + str(other)

    def __ge__(self, other):
        return self._name + ">=" + str(other)


class Table(object):
    """ Table class represents the database table """
    
    def __init__(self, name):
        self._name = name
        self._path_arr = [name, None]

    def __getattr__(self, column):
        return Column(column, self._name)


class SQL(object):
    
    def __init__(self, db):
        """Initializes the sql object. db object is needed for initialization.
        db object isn't a specific database object, it needs to be defined 
        outside SQL class, SQL class only needs the db.put() and db.get()
        
        This is an example of having a db class if using MySQLdb module
        
        class DB(object):
            def __init__(self):
                # init a mysql db object here.
                
            def put(self, sql):
                # calls sql statement by db.cursor.execute()
                
            def get(self, sql):
                # calls sql statement by db.cursor.execute() and fetchall()
                
        So the DB() can be used like this:
        
        >>> db = DB(..) # can be some init info here
        >>> sql = SQL(db)
        >>> sql.select(..) # whatever you wanna do here.
        
        Args:
            db: db object. The db object should have API: get() and put()
        """
        self._db = db

    def _logical_operator(self, arr, counter):
        """This function iterately calls itself to genterate the AND and OR 
        logical. Generator would use AND or OR alternately by layers, for 
        example:
        
        >>> A==1, B==2
        ... `A=1 and B=2`
        
        >>> A==1, B==2, (C<10, D>20)
        ... `A=1 and B=2 (C<10 or D>20)`
        
        >>> A==1, B==2, (C<10, D>20, (E='a', F=12))
        ... `A==1 and B==2 and (C<10 or D>20 or (E='a' and F=12))`
        
        you can see that Or and And are used alternately by layers.
        
        Args:
            arr : is the list of condition such as A==B, C<10
            counter: records the layer of the iteration
        Returns:
            string        
        """
        counter += 1
        _arr = []
        for a in arr:
            if type(a) == tuple:
                ret = self._logical_operator(a, counter)
                _arr.append(ret)
            else:
                _arr.append(str(a))
        if counter % 2 == 0:
            ret = '(%s)'%(' AND '.join(_arr))
        else:
            ret = '(%s)'%(' OR '.join(_arr))
        return ret
    
    def _where(self, *where):
        """Generates WHERE statement.

        Args:
            *where: the condition tuples
        Returns:
            where statement.
        """
        if not where:
            where = ""
        else:
            where = 'WHERE '+ self._logical_operator(where, 0)
        return where

    def select(self, obj, *where):
        """SQL select.

        Args:
            obj: the 
            *where: condition
        """
        table, column = obj._path_arr
        if not column:
            column = "*"
        where = self._where(where)
        sql = "SELECT %s FROM %s %s" % (column, table, where)
        return self._db.get(sql)
    
    def insert(self, table, isignored = False, **kwargs):
        """SQL insert. Rules:

        sql.update($table_name, isignored = bool, [$keys, $values])
        
        Args:
            table: the Table object.
            **kwargs: the insert info in dictionary
        """
        columns = ','.join(kwargs.keys())
        values = []
        for val in kwargs.values():
            if type(val) == str:
                val = "'%s'" % val
            else:
                val = str(val)
            values.append(val)
        values = ','.join(values)
        if isignored:
            ignore = ' IGNORE'
        else:
            ignore = ''
        sql = "INSERT%s INTO %s (%s) VALUES (%s)" % (ignore, table._name, columns, values)
        self._db.put(sql)
        
    def update(self, table, *where, **kwargs):
        """SQL update. Rules:
        
        sql.update($table_name, [$condition1, condition2, ..], [$keys, $values])

        Args:
            table: the Table object
            *where: condition
            **kwargs: the update info in dictionary
        """
        where = self._where(where)
        setting = []
        for key in kwargs:
            val = kwargs[key]
            if type(val) == str:
                val = "'%s'" % val
            else:
                val = str(val)
            single_set = '%s=%s' % (key, val)
            setting.append(single_set)
        sets = ','.join(setting)
        sql = "UPDATE %s SET %s %s" % (table._name, sets, where)
        self._db.put(sql)

