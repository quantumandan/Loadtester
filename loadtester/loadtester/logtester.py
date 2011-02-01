from logparser import MalformedEntryException
from itertools import cycle, islice
import httplib2
import time

class LogTester(object):
    """
    Used to iterate over a list of logs in a roundrobin, performing
    a test on each log entry.  LogTester's "test" method is meant to
    be overridden by some subclass.
    """
    
    def __init__(self, logs):
        # self.logs is an iterable of logs
        self.logs = logs
        self.number_tests = 0
        self.number_malformed = 0
          
    def readlines(self, count=-1, timeout=-1.0):
        """
        roundrobin recipe derived from George Sakkis'
        """
        pending = len(self.logs)
        nexts = cycle(iter(log).next for log in self.logs)
        starttime = time.time()
        while pending:
            try:
                for next in nexts:
                    # first check for number of tests executed, then check
                    # runtime, if runtime in minutes is greater than the
                    # timeout then stop executing
                    runtime = (time.time() - starttime) / 60.0
                    if self.number_tests == count:
                        raise StopIteration
                    elif (timeout != -1.0) and (runtime > timeout):
                        raise StopIteration
                    self.number_tests += 1
                    yield next()
            except StopIteration:
                pending -= 1
                nexts = cycle(islice(nexts, pending))

    def doTest(self, count=-1, timeout=-1):
        for entrydata in self.readlines(count=count, timeout=timeout):
            try:
                output = self.test(entrydata)
                yield output
            except MalformedEntryException:
                self.number_malformed += 1

    def test(self, *args, **kwargs):
        raise NotImplementedError
    
        
        
