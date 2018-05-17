# Pensieve Recreation for CS244
This is a fork of the Pensieve Github which we are using to recreate and extend two
figures presented in the original Pensieve paper (Figures 11 and 13).

### Prerequisites
- Install prerequisites (tested with Ubuntu 16.04, Tensorflow v1.1.0, TFLearn v0.3.1 and Selenium v2.39.0)
```
python setup.py
```

Note that the above will set up an Apache server and load files to serve into the /var/www/html directory

### Set up a real world test

Navigate to real_exp/

```
python real_world_run_video.py RL 1000 1
```

(Replace RL with the appropriate ABR algorithm if you don't want to test Pensieve)
