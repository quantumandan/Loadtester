from datetime import timedelta, datetime
from itertools import groupby
import re
import time
from itertools import ifilter, ifilterfalse


class TimeStamp(object):
    """
    Nginx logs have time stamps with format %d/%b/20%y:%H:%M:%S
    """

    def __init__(self, timestr, format='%d/%b/20%y:%H:%M:%S'):
        self.timestr = timestr
        self.format = format
        self.time = self.toTime(timestr)

    def toNginx(self, timeobj):
        assert isinstance(timeobj, datetime)
        return time.strftime(self.format, timeobj.timetuple())
    
    def toTime(self, timestr):
        return datetime(*(time.strptime(timestr, self.format)[0:6]))

    def increment(self, **kwargs):
        """
        kwargs ie: minutes=1, seconds=20
        """
        delta = timedelta(**kwargs)
        self.time = self.time + delta
        self.timestr = self.toNginx(self.time)
        return self
    
    def __cmp__(self, x):
        return cmp(self.time, x.time)
    
    def __eq__(self, x):
        try:
            return self.time == x.time
        except:
            return False
        
    def __str__(self):
        return self.timestr
    
    __repr__ = __str__
    

class NginxTimeStamp(object):
    """
    used to wrap a time stamp.  precision defaults to seconds
    """
    
    pattern = '(([0-9]{2})\/([A-Za-z]+)\/([0-9]{4}))(:[0-9]{2}){3}'
    
    def __init__(self, line, accuracy='seconds'):
        self.timestr = search(self.pattern, line)
        self.line = line

        if precision == 'seconds':
            format = '%d/%b/20%y:%H:%M:%S'
            idx = None
        elif precision == 'minutes':
            format='%d/%b/20%y:%H:%M'
            idx = -3
        elif precision == 'hours':
            format='%d/%b/20%y:%H'
            idx = -6
        else:
            raise 'Invalid time window'
        
        self.timestamp = TimeStamp(self.timestr[:idx], format=format)
        
    def __eq__(self, x):
        try:
            return self.timestamp == x.timestamp
        except:
            return False
        
    def __str__(self):
        return self.timestamp.timestr

    __repr__ = __str__
    
    
def NginxTimeWindow(data, window_type):
    """
    Uses parsed nginx time stamps to group entries with
    time stamps that lie inside a common time window.
    window_type can be 'seconds', 'minutes', or 'hours'
    """
    timestamps = (NginxTimeStamp(x, window_type) for x in iter(data))
    return groupby(timestamps)

def search(pattern, string):
    r = re.compile(pattern)
    searched = r.search(string)
    if searched: return searched.group()
    else: return ''

def threshold(data, cap, window_type):
    """
    picks out only those times when the number of requests
    per window_type (precision) are greater than the cap.
    this can be used to pull out all the entries inside each 
    time window where the number of entries is greater than N.
    data is an iterable. window_type can be 'seconds',
    'minutes', or 'hours', yields actual line from data,
    not parsed dictionary of fields/values
    """
    _len = len                         # optimization
    for k, g in NginxTimeWindow(data, window_type):
        v = [x.line for x in g]
        if _len(v) >= cap:
            for line in v:
                yield line
        else:
            continue
        
def keepOnly(log, predicate):
    """
    takes logentries, filters them, returning
    an itertools obj which yields each line of data parsed
    as a dictionary.  works similar to itertools takewhile, ie
    predicate = lambda parsed: parsed['status'].strip('"') == '200'
    """
    return ifilter(predicate, log)

def excludeOnly(log, predicate):
    """
    works similar to itertools takewhile
    """
    return ifilterfalse(predicate, log)
