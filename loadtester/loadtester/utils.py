import sys
from itertools import tee


class Iterator(object):
    """ Docstring for Iterator"""
    def __init__(self, iterable, loop='while'):
        self._a, self._b = tee(iter(iterable), 2)
        self.loop = loop
        self._previous = None
        self._peeked   = self._b.next()
    
    def __iter__(self):
        return self
    
    def next(self):
        """
        """
        self._previous = self._a.next()
        self._current = self._peeked
        try:
            self._peeked = self._b.next()
        except StopIteration:
            self._peeked = None
        if self.loop == 'while':
            return self._current
        elif self.loop == 'for':
            return self._previous, self._current, self._peeked
        else:
            raise ValueError, "loop type must be either 'for' or 'while'"
        
    def prev(self):
        """
        Initialized to None
        """
        return self._previous
    
    def peek(self):
        return self._peeked


class Window(object):
    """Intended to be used inside a for or while loop"""
    def __init__(self, iterable):
        self._a, self._b = tee(iter(iterable), 2)
        self._previous = None
        self._peeked   = self._b.next()
    
    def __iter__(self):
        return self
    
    def next(self):
        _prev = self._previous
        self._previous = self._a.next()
        self._current = self._peeked
        try:
            self._peeked = self._b.next()
        except StopIteration:
            self._peeked = None
        return _prev, self._current, self._peeked
        
    def prev(self): return self._previous
    
    def peek(self): return self._peeked

                
def passedWith(resp, entry, delta):
    """ """
    def _write(string):
        for line in string:
            sys.stdout.write(line)
    
    def _test(resp, entry):
        if str(resp.status) != str(entry['status']):
            return False
        else:
            return True
    
    error_string = (
        '\n----- Status is %s %s but does not match the recorded value of %s\n' % (resp.status, resp.reason, entry['status']),
        'Resource Was: %s\n' % (entry['resource'],),
        'timedelta: %s\n' % (delta,),
            )
    passed_string = '\n----- ** test passed with %s %s ** timedelta: %s\n' % (resp.status, resp.reason, delta)
    
    tv = _test(resp, entry)
    
    if tv:
        _write(passed_string)
    else:
        _write(error_string)
    
    if str(resp.status)[0] == '3':
        try:
            while resp:
                sys.stdout.write('==> Redirect to: %s \n' % resp['location'])
                resp = resp.previous
        except:
            sys.stdout.write('Cannot resolve url for redirected resource')


##############################################################################
# The following are included for python2.4 compatability
##############################################################################

def any(iterable):
    for e in iterable:
        if e:
            return True
    return False

def all(iterable):
    for element in iterable:
        if not element:
            return False
    return True
