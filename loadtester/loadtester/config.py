from optparse import OptionParser
import ConfigParser
import os


DEFAULT_TEMPLATE = '$remote_addr - $remote_user [$time_local] $request "$status" $body_bytes_sent "$http_referer" "$http_user_agent" "$http_x_forwarded_for"'
DEFAULT_REGEX = {'remote_addr':'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}',
             'remote_user':'\-',
             'time_local':'\[(([0-9]{2})\/([A-Za-z]+)\/([0-9]{4}))(:[0-9]{2}){3}\s-[0-9]{4}\]',
             'request':'(GET|OPTIONS|HEAD) \/(.*) (HTTP\/([1-9](\.[0-9])?)?)',
             'status':'\"[1-5][0-9]{2}\"',
             'body_bytes_sent':'\s[0-9]+\s',
             'http_referer':'\"(http:\/\/.*?|-)\"',
             'http_user_agent':'\"([A-Za-z]+\/([1-9](\.[0-9])?)? \(.*\) .*?)\"',
             'http_x_forwarded_for':'\-'
             }
DEFAULT_PATTERN = '.*'

class LogConfigParser(object):
    """
    If log.cfg cannot be found then the defaults are used.  Note that if the destination
    ends with '/', such as in http://example.com/, it will be stripped out.  Here in config
    is the only place where this occur.
    """
    def __init__(self, filename='log.cfg'):
        self.cfg = ConfigParser.RawConfigParser()
        self.cfg.read(filename)
    
    def regex(self):
        try:
            return dict(self.cfg.items('regex'))
        except ConfigParser.NoSectionError:
            return DEFAULT_REGEX
    
    def template(self):
        try:
            return self.cfg.get('template', 'log_template')
        except ConfigParser.NoSectionError:
            return DEFAULT_TEMPLATE


class ReplayConfigParser(object):
    """ Docstring for ReplayConfigParser"""
    def __init__(self, filename):
        self.cfg = ConfigParser.RawConfigParser({'input':filename, 'grepargs':'.*'})
        self.cfg.read(filename)
        
    def batch(self):
        """
        returns dictionary of dictionaries:
        ie {'http://geography.unc.edu':{input:'...', 'grepargs':'...'}, ...}
        """
        d = {}
        try:
            for s in self.cfg.sections():
                # make sure to strip out '/'
                d[s.strip('/')] = dict(self.cfg.items(s))
            return d
        except ConfigParser.NoSectionError:
            return None
    
    
def configure():
    # Create parser for command line options
    parser = OptionParser()
    
    # Get filename/resolve path
    parser.add_option("-f", "--file", dest="input", type="string",
                      help="Specifies path+log filename if other than host.access.log", 
                      metavar="FILE", default='host.access.log')
   
    parser.add_option("-o", "--output", dest="output", type="string",
                      help="Name of csv file to contain output data")

    parser.add_option("-H", "--host", dest="host", type="string",
                    help="Sets host in the header", metavar="HOST")

    parser.add_option("-d", "--destination", dest="destination", type="string",
                    help="Manually sets ip", metavar="destination")

    parser.add_option("-g", "--grep", dest="grepargs", type="string",
                    help="Sets arguments to grep", metavar="grepargs", default=DEFAULT_PATTERN)

    parser.add_option("-n", "--number", dest="number", type="int",
                    help="Cap number of lines read", default=-1)

    parser.add_option("-v", "--verbose", dest="verbose",
                      help="Verbose logging", action='store_true', default=False)
                      
    parser.add_option("-r", "--redirect", dest="follow_redirects",
                      help="Follow redirects", action='store_true', default=False)

    parser.add_option("-b", "--batch", dest="batch_file",
                      help="Name of batch file")

    parser.add_option("-c", "--cfg", dest="cfg_file", type="string",
                      help="Name of log cfg file", default='log.cfg')

    parser.add_option("-t", "--timeout", dest="timeout", type="float",
                      help="Number of minutes before timeout", default=-1.0)
                      
    parser.add_option("-p", "--processes", dest="processes", type="int",
                      help="Number of processes to run in the background", default=1)

    (options, args) = parser.parse_args()

    logParser = LogConfigParser(options.cfg_file)
    if options.batch_file:
        replayParser = ReplayConfigParser(options.batch_file)
        batched = replayParser.batch()
    else:
        # in case the user messes up, don't forget
        # to strip '/' from the end of destination
        batched = {
            options.destination.strip('/'):{
                    'input':options.input, 
                    'output':options.output,
                    'grepargs':options.grepargs,
                    'follow_redirects':options.follow_redirects,
                    'host':options.host
                    }
                }
    return logParser.template(), logParser.regex(), batched, options
    

