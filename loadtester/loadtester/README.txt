Description:
Loadtester is a general purpose tool for working with a variety of log files,
with a focus on Nginx access logs.  It is a command line utility that allows
the user to 'replay' access logs.  Provided is an API for parsing, verifying,
testing, and replaying log files.

Installation:
Optional -- create virtualenv (using python 2.4 or greater but less than 3)
easy_install httplib2

git (via ssh) git@github.com:quantumandan/Loadtester.git
or
git (via http) https://quantumandan@github.com/quantumandan/Loadtester.git

python setup.py install (can also run with the 'develop' option)

Setup:
Out of the box loadtester works with the nginx's default log template.  However, if using a 
custom log format or to change the regular expressions (python dialect) used to parse the log, you
must create a file called log.cfg.  Below is a sample log.cfg replicating loadtester's default setup:

    [template]
    log_template = $remote_addr - $remote_user [$time_local] $request "$status" $body_bytes_sent "$http_referer" "$http_user_agent" "$http_x_forwarded_for"
    
    [regex]
    remote_addr = \d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}
    remote_user = \-
    time_local = \[(([0-9]{2})\/([A-Za-z]+)\/([0-9]{4}))(:[0-9]{2}){3}\s-[0-9]{4}\]
    request = (GET|OPTIONS|HEAD) \/(.*) (HTTP\/([1-9](\.[0-9])?)?)
    status = \"[1-5][0-9]{2}\"
    body_bytes_sent = \s[0-9]+\s
    http_referer = \"(http:\/\/.*?|-)\"
    http_user_agent = \"([A-Za-z]+\/([1-9](\.[0-9])?)? \(.*\) .*?)\"
    http_x_forwarded_for = \-

Each $ denoted field in template MUST have a corresponding regular expression in regex.  Also, 
do NOT use interpolation as it may affect how the ConfigParser gets the regular expressions.

Usage:
Loadtester may be run in one of two single process modes - standard and batch.  Standard mode 
operates on one log at a time, whereas batch mode handles multiple logs in a round robin fashion. For example,

    standard:
    loadtester -f .../path/to/host.access.log -d http://geography.unc.edu -o output.csv

    batch:
    loadtester -b replay.cfg -o output.csv

Alternatively, the "lt" command can be used to run multiple processes of loadtester in batch mode.
For example:

    lt -b replay.cfg -p 10 -n 100

will run 10 processes of loadtester, running the first 100 entries (in total) from each log indicated
in replay.cfg.  The lt command will create a directory called diagnostic-data populated with csv files
named process0.csv, process1.csv, etc for each process.  For csv format see Output section at the bottom.

Running in batch mode requires a cfg file (see example below):

    [http://localhost:9410/w_geography/geography]
    filename = .../dev/data/geography.unc.edu/logs/host.access.log

    [http://localhost:9410/w_learningcenter/learningcenter]
    filename = .../dev/data/learningcenter.unc.edu/logs/host.access.log

A note about the lt command -- Unfortunately, loadtester is not multithreaded.  We get around 
this problem by running multiple concurrent processes in the background.  The lt command 
generates a bash script which runs loadtester in the background and then starts the script.
Because lt creates files and a directory, and it runs a script, you will need to be root to
successfully run lt.  Another consequence is that the lt command works ONLY on LINUX and OSX.

Command Line Options:
    -f or --file, Specifies path + log file name if other than host.access.log
    -H or --host, Sets host header
    -d or --destination, Sets target ip/domain of site we are testing against
    -g or --grep, Python regular expression to extract a subset of the data
    -n or --number, Caps number of lines read in total
    -t or --timeout, Sets timeout in minutes
    -r or --redirect, Determines whether or not to follow redirects
    -o or --output, Creates csv file of output data with the specified name
    -b or --batch, Run in batch mode using the specified cfg file

A note about grepargs -- python automatically converts spaces in regular expressions to \s.  
Therefore it is fine to include spaces when using the grepargs field in batch mode.  
However, if running in standard mode, spaces must be explicitly coded as \s or loadtester will 
incorrectly parse the command line arguments.

Output:
The ouput will be a csv file (without column headers) which has the fields:

Python 2.5 or greater --
[timestamp,destination,resource,status_recorded,status_recieved,timedelta,content-length]

Python 2.4 --
[destination,resource,status_recorded,status_recieved,timedelta,content-length]

Where timestamp is the Hour:Minute:Second the request was made, status_recorded is the 
status listed in the nginx log, status_recieved is the status recieved from the test,
and timedelta is the time it took to make the request in milliseconds.




