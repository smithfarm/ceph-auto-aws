#
# runner_lib.py
#
# runcommand() for running executables in a subprocess or shell
#
# Credits to Owen Synge <osynge@suse.com>
#

import sys
import subprocess
import time

def runcommand(*args, **kwargs):
    cmd = kwargs.get('cmd', None)
    shell = kwargs.get('shell', None)
    arguments = kwargs.get('arguments', [])
    timeout = kwargs.get('timeout', 10)
    if shell != False:
        shell = True
    cmdargs = [str(cmd)] + arguments
    #print "cmdargs == {}".format(cmdargs)
    try:
        process = subprocess.Popen(cmdargs, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except:
        sys.stderr.write("Failed to execute %s" % repr(cmdargs))
        raise

    processRc = None
    handleprocess = True
    counter = 0
    stdout = ''
    stderr = ''
    while handleprocess:
        counter += 1
        time.sleep(1)
        cout,cerr = process.communicate()
        stdout += cout
        stderr += cerr
        process.poll()
        processRc = process.returncode
        if processRc != None:
            break
        if counter == timeout:
            os.kill(process.pid, signal.SIGQUIT)
        if counter > timeout:
            os.kill(process.pid, signal.SIGKILL)
            processRc = -9
            break
    return (processRc,stdout,stderr)

