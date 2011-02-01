import subprocess
import shutil
import config
import os
from os.path import join

def main():
    
    template, regex, batch, options = config.configure()

    BASE_CMD = 'loadtester -b %s -o diagnostic-data/process%s.csv'

    # make directory structure
    cwd = os.getcwd()
    try:
        shutil.rmtree(join(cwd, 'diagnostic-data'))
    except:
        pass
    os.mkdir(join(cwd, 'diagnostic-data'))
    
    # form commands
    cmd = BASE_CMD
    cmds = [cmd % (options.batch_file, p) for p in range(options.processes)]
    if options.number:
        cmds = [c + ' -n %s' % options.number for c in cmds]
    if options.timeout:
        cmds = [c + ' -t %s' % options.timeout for c in cmds]
    if options.grepargs:
        cmds = [c + ' -g %s' % options.grepargs for c in cmds]
    if options.follow_redirects:
        cmds = [c + ' -r %s' % options.follow_redirects for c in cmds]
    if options.host:
        cmds = [c + ' -H %s' % options.host for c in cmds]
    if options.cfg_file:
        cmds = [c + ' -c %s' % options.cfg_file for c in cmds]
    cmds = [c + ' &' for c in cmds]
        
    # generate shell script
    script = open('_ltstart.sh', 'w')
    try:
        shell = '#!/bin/sh'
        for c in cmds:
            shell = shell + '\n' + c
        script.write(shell)
    finally:
        script.close()
    
    # finish up and run
    path_to_executable = join(cwd, '_ltstart.sh')
    os.chmod(path_to_executable, 755)
    p = subprocess.call([path_to_executable])
    print 'return code is: ', p


if __name__ == '__main__':
    main()
    
    
