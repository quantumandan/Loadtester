from sanitychecker import RegTemplate
import re


def pygrep(data, pattern):
    """
    Poor man's grep, returns a generator.
    """
    g = re.compile(pattern)
    return (line for line in data if g.search(line))

#####################################################################
# Errors
#####################################################################
class MalformedEntryException(Exception):
    pass

#####################################################################
# Log File classes:
# xLog (sub)classes are fault tolerant which means they are tolerant of
# slight errors in the regular expressions or slight deviations
# in the log data from it's template -- both of which may contribute
# to an only partially successful parsing.  A log does it's best to find 
# all the parts indicated by the template, but does not throw any
# errors if it cannot -- those skipped parts will recieve a None value.
#####################################################################
class Log(object):
    """
    Base log class.
    """
    def __init__(self, data, log_template, regex_dict):
        self.log_template = log_template
        self.regex_dict = regex_dict
        self.data = data
        self.Template = RegTemplate(log_template)
        self.Template.compile(regex_dict)


class xLog(Log):
    """
    Fault tolerant log class. Intended to be used with pygrep.
    """
    def __init__(self, data, log_template, regex_dict):
        super(xLog, self).__init__(data, log_template, regex_dict)

    def __iter__(self):
        return self

    def next(self):
        line = self.data.next()
        # using xgroupdict as opposed to groupdict
        # makes the log more tolerant of 
        # irregularites in the regular expressions
        return self.Template.xgroupdict(line)


class xLogFile(xLog):
    """
    Fault tolerant log file.  Intended to be used only with a 
    file-like object (such as a file or StringIO) that supports
    .seek() and .tell() methods. TODO add incremental caching
    of bytes in a 'next' method instead of caching all at once 
    inside the constructor.
    """
    def __init__(self, fileobj, log_template, regex_dict):
        super(xLogFile, self).__init__(fileobj, log_template, regex_dict)
        self.cache = set()
        # run through the data, associating linenumbers to bytes
        lineno = 0
        for l in self.data:
            self.cache.add((lineno, self.data.tell()))
            lineno += 1
        # reset file
        self.data.seek(0)
        
    def __getitem__(self, target_lineno):
        """
        Might be slow depending on log size
        """
        f = self.data
        # get starting position
        current_pos = f.tell()
        # rewind the file
        f.seek(0)
        
        def getLine():  
            if target_lineno < 0:
                raise IndexError, 'Indexing starts at 0'
            cached = self._getByte(target_lineno)
            if cached:
                return f.seek(cached).next()
            else:
                raise IndexError, 'Index out of bounds'
            
        try:
            line = getLine()
        finally:
            # return to starting position
            f.seek(current_pos)
        return line

    def _getByte(self, linenumber):
        return [x[1] for x in self.cache if int(linenumber) == int(x[0])]
        
    
#####################################################################
# LogEntry classes:
#####################################################################
class LogEntry(dict):
    """
    Basic log entry class.
    """
    def __init__(self, data_dict, **kwargs):
        # parse data_dict before setting key, value pairs
        for field, value in data_dict.iteritems():
            self[field] = self.parse(field, value)
        # include any additional key, value pairs
        # passed in via kwargs
        if kwargs:
            for field, value in kwargs.iteritems():
                self[field] = value
                               
    def parse(self, field, value):
        return value


class NginxLogEntry(LogEntry):
    """
    Takes nginx logentry, parses it, and returns the data as
    attributes on the instance
    """
    def __init__(self, data, **kwargs):
        super(NginxLogEntry, self).__init__(data, **kwargs)
        try:
            self['method'], self['resource'], self['http'] = data['request'].split(' ')
        except ValueError:
            raise MalformedEntryException
        except KeyError:
            # happens if using csv data that contains
            # method and resource rather than the request
            assert 'method' in self
            assert 'resource' in self

    def parse(self, field, value):
        """
        The only thing required to replay and test an nginx logentry
        is the request and the status.
        """
        try:
            # Can't connect if request is None
            if field == 'request' and value is None:
                raise MalformedEntryException
            # Can't pass tests if status is None
            elif field == 'status' and value is None:
                raise MalformedEntryException
            return value.replace('"', '').strip()
        except AttributeError:
            return ''
        
        
