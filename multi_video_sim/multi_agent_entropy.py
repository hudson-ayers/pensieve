# Script for running the multi video training model with automatically decreasing entropy weight
import os
import glob
import subprocess
from time import sleep


def last_model():
	model_list = glob.glob('./models/nn_model_ep_*.ckpt*')
	highest_model = 100
	for model_file in model_list:
		iteration_num = int(model_file.replace("./models/nn_model_ep_", "").split(".ckpt")[0])
		if iteration_num > highest_model:
		        highest_model = iteration_num
	return highest_model
		

def run():

	os.environ['last_model']='None'
	os.environ['ENTROPY_WEIGHT']='5'
	FNULL = open(os.devnull, 'w')


	while(True):
		command = 'exec /usr/bin/python ./multi_agent.py'
		proc = subprocess.Popen(command, shell=True, stderr=FNULL)
		sleep(180) #Sleep 1 hour at a time
		proc.kill()
		last_itr_num = last_model()
		print "last iteration: " + str(last_itr_num)
		os.environ['last_model']='nn_model_ep_' + str(last_itr_num) + '.ckpt'
		if (last_itr_num < 300):
		        pass
		elif (last_itr_num < 600):
   		        os.environ['ENTROPY_WEIGHT']='1'
		elif (last_itr_num < 80000):
		        os.environ['ENTROPY_WEIGHT']='0.5'
		elif (last_itr_num < 100000):
		        os.environ['ENTROPY_WEIGHT']='0.3'
		elif (last_itr_num < 120000):
		        os.environ['ENTROPY_WEIGHT']='0.1'
		else:
		        break
	return 0


if __name__ == "__main__":
	run()
