#! /bin/bash

mkdir old_results

for i in {0..120}
do
    python2 ./real_world_run_video.py RL 480 1
    mkdir ./old_results/RL_TEST_$i
    mv ./results/* ./old_results/RL_TEST_$i
    fuser -k -n tcp 8333
    python2 ./real_world_run_video.py robustMPC 480 1
    mkdir ./old_results/robustMPC_TEST_$i
    mv ./results/* ./old_results/robustMPC_TEST_$i
    fuser -k -n tcp 8334
    python2 ./real_world_run_video.py BOLA 480 1
    mkdir ./old_results/BOLA_TEST_$i
    mv ./results/* ./old_results/BOLA_TEST_$i
    fuser -k -n tcp 8335
done
