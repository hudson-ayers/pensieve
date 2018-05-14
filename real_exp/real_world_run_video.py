import os
import sys
import signal
import subprocess
from time import sleep

abr_algo = sys.argv[1]
run_time = int(sys.argv[2])
exp_id = sys.argv[3]

try:


        command1 = 'lsof -ti:8333 | xargs kill -9'

	# start abr algorithm server
	if abr_algo == 'RL':
		command = 'exec /usr/bin/python ../rl_server/rl_server_no_training.py ' + exp_id
	elif abr_algo == 'fastMPC':
		command = 'exec /usr/bin/python ../rl_server/mpc_server.py ' + exp_id
	elif abr_algo == 'robustMPC':
		command = 'exec /usr/bin/python ../rl_server/robust_mpc_server.py ' + exp_id
	else:
		command = 'exec /usr/bin/python ../rl_server/simple_server.py ' + abr_algo + ' ' + exp_id
	
        #Following 4 lines added to address frequent "ADDR ALREADY IN USE" errors
        proc1 = subprocess.Popen(command1, shell=True)
        sleep(1)
        proc1.kill()
        
        proc = subprocess.Popen(command, shell=True)
	sleep(2)
        
	
	sleep(run_time)
	
	print 'done'

        proc.send_signal(signal.SIGINT)
	
except Exception as e:
	try:
		proc.send_signal(signal.SIGINT)
	except:
		pass
	
	print e	

