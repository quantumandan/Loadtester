from logparser import xLog, pygrep, NginxLogEntry
from logtester import LogTester
import time
from datetime import datetime
import config
import csv
import httplib2

"""
Used for running quick diagnostics directly from nginx access logs.

loadtester -b batch.cfg -t 60 -n 10000 -g 12/Jan/2010

The above command runs the loadtester and will stop testing after 60 minutes or 10,000 
lines (whichever comes first).  The -g option will grep through each entry searching for, 
in this case, all the entries which have the timestamp 12/Jan/2010.

Note that the processed log will be a csv file (without column headers) which has the fields:

Python 2.5 or greater:
[timestamp,destination,resource,status_recorded,status_recieved,timedelta,content-length]

Python 2.4
[destination,resource,status_recorded,status_recieved,timedelta,content-length]
"""
     
class MultiLogWrapper(object):
    """
    modifies iterator to return data in tuple suitable for running a test
    against multiple sites
    """
    def __init__(self, destination, data):
        self.destination = destination.strip('/')
        self.data = data

    def __iter__(self):
        return self
    
    def next(self):
        return self.destination, self.data.next()
    
    
class HttpLoadTester(LogTester):
    """
    Input logs must be a list of objects with the following properties:
    each object must be iterable and its 'next' method must provide a tuple
    (destination, dictionary-like object) where the dictionary-like object
    must have keys 'resource' and 'method'.  The easiest way to satisfy this
    requirement is to use MultiLogWrapper or some subclass of it in conjuction with
    csv.DictReader (when running with processed csv data) or xLog (when running
    with nginx access logs).
    """
    
    def __init__(self, logs, options):
        super(HttpLoadTester, self).__init__(logs)
        self._http = httplib2.Http()
        self.options = options

    def test(self, logdata):
        """
        Throws MalformedEntryException if entry creation fails
        """
        # logdata is a tuple of (destination, data_dict) yielded
        # when running LogTester on wrapped (MultiLogWrapper) data
        destination, data_dict = logdata
        # throws MalformedEntryException if entry creation fails
        entry = NginxLogEntry(data_dict)
        resp, content, delta = self.replay(destination, entry['resource'], entry['method'])
        # convert timedelta from seconds to milliseconds
        delta = int(float(delta) * 1000)
        return destination, resp, entry, delta

    def replay(self, destination, resource, method):
        """
        Takes full path to a resource and a method, then recreates the
        request.  Returns response, content, and timedelta as a tuple.
        """
        headers = {}
        # httplib2 is funny when it comes to setting the host header.
        # If using the default host, do not include a host header.
        if self.options.host is not None:
            headers['host'] = self.options.host
        self._http.follow_redirects = self.options.follow_redirects
        try:
            target = destination.strip('/') + resource
            start = time.time()
            resp, content = self._http.request(target, method, headers=headers)
            stop = time.time()
        except AttributeError:
            raise 'Cannot connect to server'
        return resp, content, stop - start


DATETIMEFORMAT = '%a, %d %b 20%y %H:%M:%S %Z'


def main():
    # remember, batch is a dictionary of dictionaries ie
    # {'http://geography.unc.edu':{filename:'...', 'grepargs':'...'}, ...}
    template, regex, batch, options = config.configure()

    # tuples with the following form:
    # [(dest1, fileobj1), (dest2, fileobj2), ...]
    args = [(k, open(batch[k]['input'], 'r')) for k in batch]

    # prep for generating log wrappers
    # [(destination1, data1), (destination2, data2), ...]
    data = [(a[0], pygrep(a[1], options.grepargs)) for a in args]

    # make list of wrapped logs
    logs = [MultiLogWrapper(d[0], xLog(d[1], template, regex)) for d in data]

    # instantiate tester and start testing
    tester = HttpLoadTester(logs, options)
    
    # prepare output csv file
    csv_file = open(options.output, 'w')
    
    # [destination,resource,status_recorded,status_recieved,timedelta,timestamp,content-length]
    writer = csv.writer(csv_file)
    
    # start testing
    print '\nStarting tests at %s' % time.ctime()
    print 'Warning this may take awhile.'
    start = time.time()
    timedeltas = [float(0)]
    long_urls = []
    try:
        for destination, resp, entry, delta in tester.doTest(count=options.number, timeout=options.timeout):
            long_urls.append((delta, entry['resource'], resp.status))
            if resp.status == 200:
                timedeltas.append(delta)
                print '**  test passed -- timedelta: %s ms **' % delta
            else:
                timedeltas.append(delta)
                print '**  test failed with status: %s -- timedelta %s ms' % (resp.status, delta)
            # write data to csv file
            try:
                d = datetime.strptime(resp['date'], DATETIMEFORMAT)
                datetimestr = '%s:%s:%s' % (d.hour, d.minute, d.second)
                writer.writerow([datetimestr, destination, entry['resource'], entry['status'], resp.status, delta, resp['content-length']])
            except AttributeError:
                writer.writerow([destination, entry['resource'], entry['status'], resp.status, delta, resp['content-length']])
    finally:
        [f[1].close() for f in args]
        csv_file.close()
        stop = time.time()
        tm = round(stop - start, 2)
        number_tests = tester.number_tests
        number_malformed = tester.number_malformed
        if tm != 0:
            requests_per_second = round(float(number_tests) / float(tm), 2)
        else:
            requests_per_second = 0
        # calculate avg of timedeltas
        if number_tests != 0:
            avg_timedelta = round(float(sum(timedeltas))/float(number_tests), 2)
        else:
            avg_timedelta = 'N/A'
            
        print '\n'
        print '######################################################'
        print 'top 5 longest urls:'
        long_urls.sort(key=lambda x: x[0])
        for s in long_urls[-5:]:
            print '** timedelta: %s ms, status: %s' % (s[0], s[2])
            print '==> resource: %s' % s[1]
        print '\n'
        print 'avg timedelta is %s ms' % avg_timedelta
        print 'requests per second is %s requests/seconds' % requests_per_second
        print 'number of malformed entries is: ', number_malformed
        print 'number of tests is: ', number_tests
        print 'finished testing in %s seconds' % tm
        print '######################################################'
        print '\n'
        
if __name__ == '__main__':
    main()

                
