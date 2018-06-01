import time
import os
import subprocess
from os import path


cmd = ['python', path.join(os.getcwd(), 'multi_agent.py')]
subprocess.call(cmd)

while(True):
    time.sleep(5)
    if float(os.environ['ENTROPY']) >  0.1:
        os.environ['ENTROPY'] = str(float(os.environ['ENTROPY']) - 0.1)

