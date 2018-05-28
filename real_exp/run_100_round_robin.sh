#! /bin/bash

FILE_PATH="old_results/mahimahi_lte"

mkdir old_results
mkdir $FILE_PATH

for i in {0..10}
do
    python2 ./real_world_run_video.py RL 480 1
    mv ./results/* ./$FILE_PATH/log_RL_$i
    fuser -k -n tcp 8333
    python2 ./real_world_run_video.py robustMPC 480 1
    mv ./results/* ./$FILE_PATH/log_robustMPC_$i
    fuser -k -n tcp 8334
    python2 ./real_world_run_video.py BOLA 480 1
    mv ./results/* ./$FILE_PATH/log_BOLA_$i
    fuser -k -n tcp 8335
done
