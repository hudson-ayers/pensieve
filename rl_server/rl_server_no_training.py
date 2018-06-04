#!/usr/bin/env python
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import SocketServer
import base64
import urllib
import sys
import os
import json
os.environ['CUDA_VISIBLE_DEVICES']=''

import numpy as np
import tensorflow as tf
import time
import a3c


S_INFO = 6  # bit_rate, buffer_size, rebuffering_time, bandwidth_measurement, chunk_til_video_end
S_LEN = 8  # take how many frames in the past
A_DIM = 5
VIDEO_BIT_RATE = [350,600,1000,2000,3000]  # Kbps
BITRATE_REWARD = [1, 2, 3, 12, 15]
BITRATE_REWARD_MAP = {0: 0, 350: 1, 600: 2, 1000: 3, 2000: 12, 3000: 15}
M_IN_K = 1000.0
BUFFER_NORM_FACTOR = 10.0
CHUNK_TIL_VIDEO_END_CAP = 64.0
TOTAL_VIDEO_CHUNKS = 64
DEFAULT_QUALITY = 0  # default video quality without agent
REBUF_PENALTY = 4.3  # 1 sec rebuffering -> this number of Mbps
SMOOTH_PENALTY = 1
ACTOR_LR_RATE = 0.0001
CRITIC_LR_RATE = 0.001
TRAIN_SEQ_LEN = 100  # take as a train batch
MODEL_SAVE_INTERVAL = 100
RANDOM_SEED = 42
RAND_RANGE = 1000
SUMMARY_DIR = './results'
LOG_FILE = './results/log'
# in format of time_stamp bit_rate buffer_size rebuffer_time video_chunk_size download_time reward
# NN_MODEL = None
NN_MODEL = '../rl_server/results/new_video_model.ckpt'

# video chunk sizes

size_video1 = [219272, 134208, 204651, 164461, 230942, 136746, 150366, 193697, 193362, 189146, 153391, 195591, 177177, 190923, 155030, 185660, 164741, 179442, 131632, 198676, 115285, 148044, 181978, 200708, 177663, 176815, 109489, 203211, 196841, 161524, 151656, 182521, 172804, 211407, 171710, 170866, 178753, 175461, 184494, 154382, 206330, 175870, 178679, 173567, 172998, 189473, 172737, 163181, 181882, 186151, 164281, 172026, 173011, 162488, 201781, 176856, 137099, 57015, 234214, 172494, 184405, 61936, 43268, 81580]
size_video2 = [370284, 246858, 357922, 264156, 371586, 241808, 270621, 327839, 334864, 313171, 253682, 348331, 319047, 311275, 282933, 308899, 289234, 307870, 207573, 354546, 208087, 305510, 364291, 331480, 298846, 298034, 195290, 327636, 354076, 261457, 272419, 344053, 307537, 344697, 301834, 261403, 332467, 324205, 276260, 260969, 357539, 301214, 320538, 292593, 290952, 325914, 285965, 266844, 327707, 308757, 271734, 313780, 284833, 295589, 331270, 307411, 224531, 94934, 385537, 306688, 310705, 95847, 78651, 162260]
size_video3 = [577615, 418531, 555427, 469238, 614632, 393715, 428426, 594788, 527047, 460827, 500774, 621760, 556545, 476734, 417508, 552639, 462442, 552256, 303234, 522859, 337637, 471941, 598737, 560588, 487684, 479873, 284277, 564825, 546935, 394056, 442514, 610493, 523364, 574457, 499175, 412705, 586327, 560284, 476697, 408166, 570011, 502061, 569274, 444948, 507586, 525450, 541979, 391886, 539537, 506089, 408110, 515570, 462132, 574826, 523754, 572621, 344553, 157240, 610010, 460871, 480012, 169331, 126490, 236234]
size_video4 = [1123706, 854424, 1150093, 902304, 1237428, 763515, 840707, 1279590, 930828, 996858, 950867, 1285933, 1049248, 984261, 876058, 1054391, 875132, 996451, 660126, 1032091, 626844, 949274, 1197901, 1001670, 994288, 925341, 623084, 977347, 1184694, 766276, 834528, 1285071, 1017030, 1080835, 1078945, 788728, 1165402, 1123991, 937434, 804808, 1178153, 922947, 1175468, 903392, 970351, 1094905, 931644, 854957, 1179875, 978233, 794797, 1073857, 942081, 1074761, 1033448, 1181202, 660582, 297985, 1188866, 910001, 974311, 314327, 221329, 445973]
size_video5 = [1637558, 1371111, 1684293, 1400042, 1792609, 1213669, 1191552, 1888982, 1381292, 1593129, 1384566, 1918298, 1605664, 1356382, 1278860, 1580165, 1315506, 1642869, 928190, 1416000, 865548, 1284104, 1692271, 1504744, 1484004, 1405086, 891371, 1401736, 1743545, 1084561, 1099310, 1789869, 1675658, 1636106, 1492615, 1200522, 1787763, 1690817, 1459339, 1250444, 1691788, 1403315, 1732710, 1270067, 1514363, 1615320, 1507682, 1260622, 1784654, 1352160, 1115913, 1637646, 1546975, 1637443, 1475444, 1616179, 1113960, 466635, 1727956, 1316739, 1373312, 458410, 320487, 573826]


def get_chunk_size(quality, index):
    if ( index < 0 or index > 64 ):
        return 0
    # note that the quality and video labels are inverted (i.e., quality 8 is highest and this pertains to video1)
    sizes = {4: size_video1[index], 3: size_video2[index], 2: size_video3[index], 1: size_video4[index], 0: size_video5[index]}
    return sizes[quality]

def make_request_handler(input_dict):

    class Request_Handler(BaseHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            self.input_dict = input_dict
            self.sess = input_dict['sess']
            self.log_file = input_dict['log_file']
            self.actor = input_dict['actor']
            self.critic = input_dict['critic']
            self.saver = input_dict['saver']
            self.s_batch = input_dict['s_batch']
            self.a_batch = input_dict['a_batch']
            self.r_batch = input_dict['r_batch']
            BaseHTTPRequestHandler.__init__(self, *args, **kwargs)

        def do_POST(self):
            content_length = int(self.headers['Content-Length'])
            post_data = json.loads(self.rfile.read(content_length))
            print post_data

            if ( 'pastThroughput' in post_data ):
                # @Hongzi: this is just the summary of throughput/quality at the end of the load
                # so we don't want to use this information to send back a new quality
                print "Summary: ", post_data
            else:
                # option 1. reward for just quality
                # reward = post_data['lastquality']
                # option 2. combine reward for quality and rebuffer time
                #           tune up the knob on rebuf to prevent it more
                # reward = post_data['lastquality'] - 0.1 * (post_data['RebufferTime'] - self.input_dict['last_total_rebuf'])
                # option 3. give a fixed penalty if video is stalled
                #           this can reduce the variance in reward signal
                # reward = post_data['lastquality'] - 10 * ((post_data['RebufferTime'] - self.input_dict['last_total_rebuf']) > 0)

                # option 4. use the metric in SIGCOMM MPC paper
                rebuffer_time = float(post_data['RebufferTime'] -self.input_dict['last_total_rebuf'])

                # --linear reward--
                reward = VIDEO_BIT_RATE[post_data['lastquality']] / M_IN_K \
                        - REBUF_PENALTY * rebuffer_time / M_IN_K \
                        - SMOOTH_PENALTY * np.abs(VIDEO_BIT_RATE[post_data['lastquality']] -
                                                  self.input_dict['last_bit_rate']) / M_IN_K

                # --log reward--
                # log_bit_rate = np.log(VIDEO_BIT_RATE[post_data['lastquality']] / float(VIDEO_BIT_RATE[0]))   
                # log_last_bit_rate = np.log(self.input_dict['last_bit_rate'] / float(VIDEO_BIT_RATE[0]))

                # reward = log_bit_rate \
                #          - 4.3 * rebuffer_time / M_IN_K \
                #          - SMOOTH_PENALTY * np.abs(log_bit_rate - log_last_bit_rate)

                # --hd reward--
                # reward = BITRATE_REWARD[post_data['lastquality']] \
                #         - 8 * rebuffer_time / M_IN_K - np.abs(BITRATE_REWARD[post_data['lastquality']] - BITRATE_REWARD_MAP[self.input_dict['last_bit_rate']])

                self.input_dict['last_bit_rate'] = VIDEO_BIT_RATE[post_data['lastquality']]
                self.input_dict['last_total_rebuf'] = post_data['RebufferTime']

                # retrieve previous state
                if len(self.s_batch) == 0:
                    state = [np.zeros((S_INFO, S_LEN))]
                else:
                    state = np.array(self.s_batch[-1], copy=True)

                # compute bandwidth measurement
                video_chunk_fetch_time = post_data['lastChunkFinishTime'] - post_data['lastChunkStartTime']
                video_chunk_size = post_data['lastChunkSize']

                # compute number of video chunks left
                video_chunk_remain = TOTAL_VIDEO_CHUNKS - self.input_dict['video_chunk_coount']
                self.input_dict['video_chunk_coount'] += 1

                # dequeue history record
                state = np.roll(state, -1, axis=1)

                next_video_chunk_sizes = []
                for i in xrange(A_DIM):
                    next_video_chunk_sizes.append(get_chunk_size(i, self.input_dict['video_chunk_coount']))

                # this should be S_INFO number of terms
                try:
                    state[0, -1] = VIDEO_BIT_RATE[post_data['lastquality']] / float(np.max(VIDEO_BIT_RATE))
                    state[1, -1] = post_data['buffer'] / BUFFER_NORM_FACTOR
                    state[2, -1] = float(video_chunk_size) / float(video_chunk_fetch_time) / M_IN_K  # kilo byte / ms
                    state[3, -1] = float(video_chunk_fetch_time) / M_IN_K / BUFFER_NORM_FACTOR  # 10 sec
                    state[4, :A_DIM] = np.array(next_video_chunk_sizes) / M_IN_K / M_IN_K  # mega byte
                    state[5, -1] = np.minimum(video_chunk_remain, CHUNK_TIL_VIDEO_END_CAP) / float(CHUNK_TIL_VIDEO_END_CAP)
                except ZeroDivisionError:
                    # this should occur VERY rarely (1 out of 3000), should be a dash issue
                    # in this case we ignore the observation and roll back to an eariler one
                    if len(self.s_batch) == 0:
                        state = [np.zeros((S_INFO, S_LEN))]
                    else:
                        state = np.array(self.s_batch[-1], copy=True)

                # log wall_time, bit_rate, buffer_size, rebuffer_time, video_chunk_size, download_time, reward
                self.log_file.write(str(time.time()) + '\t' +
                                    str(VIDEO_BIT_RATE[post_data['lastquality']]) + '\t' +
                                    str(post_data['buffer']) + '\t' +
                                    str(rebuffer_time / M_IN_K) + '\t' +
                                    str(video_chunk_size) + '\t' +
                                    str(video_chunk_fetch_time) + '\t' +
                                    str(reward) + '\n')
                self.log_file.flush()

                action_prob = self.actor.predict(np.reshape(state, (1, S_INFO, S_LEN)))
                action_cumsum = np.cumsum(action_prob)
                bit_rate = (action_cumsum > np.random.randint(1, RAND_RANGE) / float(RAND_RANGE)).argmax()
                # Note: we need to discretize the probability into 1/RAND_RANGE steps,
                # because there is an intrinsic discrepancy in passing single state and batch states

                # send data to html side
                send_data = str(bit_rate)

                end_of_video = False
                if ( post_data['lastRequest'] == TOTAL_VIDEO_CHUNKS ):
                    send_data = "REFRESH"
                    end_of_video = True
                    self.input_dict['last_total_rebuf'] = 0
                    self.input_dict['last_bit_rate'] = DEFAULT_QUALITY
                    self.input_dict['video_chunk_coount'] = 0
                    self.log_file.write('\n')  # so that in the log we know where video ends

                self.send_response(200)
                self.send_header('Content-Type', 'text/plain')
                self.send_header('Content-Length', len(send_data))
                self.send_header('Access-Control-Allow-Origin', "*")
                self.end_headers()
                self.wfile.write(send_data)

                # record [state, action, reward]
                # put it here after training, notice there is a shift in reward storage

                if end_of_video:
                    self.s_batch = [np.zeros((S_INFO, S_LEN))]
                else:
                    self.s_batch.append(state)

        def do_GET(self):
            print >> sys.stderr, 'GOT REQ'
            self.send_response(200)
            #self.send_header('Cache-Control', 'Cache-Control: no-cache, no-store, must-revalidate max-age=0')
            self.send_header('Cache-Control', 'max-age=3000')
            self.send_header('Content-Length', 20)
            self.end_headers()
            self.wfile.write("console.log('here');")

        def log_message(self, format, *args):
            return

    return Request_Handler


def run(server_class=HTTPServer, port=8333, log_file_path=LOG_FILE):

    np.random.seed(RANDOM_SEED)

    assert len(VIDEO_BIT_RATE) == A_DIM

    if not os.path.exists(SUMMARY_DIR):
        os.makedirs(SUMMARY_DIR)

    with tf.Session() as sess, open(log_file_path, 'wb') as log_file:

        actor = a3c.ActorNetwork(sess,
                                 state_dim=[S_INFO, S_LEN], action_dim=A_DIM,
                                 learning_rate=ACTOR_LR_RATE)
        critic = a3c.CriticNetwork(sess,
                                   state_dim=[S_INFO, S_LEN],
                                   learning_rate=CRITIC_LR_RATE)

        sess.run(tf.initialize_all_variables())
        saver = tf.train.Saver()  # save neural net parameters

        # restore neural net parameters
        nn_model = NN_MODEL
        if nn_model is not None:  # nn_model is the path to file
            saver.restore(sess, nn_model)
            print("Model restored.")

        init_action = np.zeros(A_DIM)
        init_action[DEFAULT_QUALITY] = 1

        s_batch = [np.zeros((S_INFO, S_LEN))]
        a_batch = [init_action]
        r_batch = []

        train_counter = 0

        last_bit_rate = DEFAULT_QUALITY
        last_total_rebuf = 0
        # need this storage, because observation only contains total rebuffering time
        # we compute the difference to get

        video_chunk_count = 0

        input_dict = {'sess': sess, 'log_file': log_file,
                      'actor': actor, 'critic': critic,
                      'saver': saver, 'train_counter': train_counter,
                      'last_bit_rate': last_bit_rate,
                      'last_total_rebuf': last_total_rebuf,
                      'video_chunk_coount': video_chunk_count,
                      's_batch': s_batch, 'a_batch': a_batch, 'r_batch': r_batch}

        # interface to abr_rl server
        handler_class = make_request_handler(input_dict=input_dict)

        server_address = ('0.0.0.0', port)
        httpd = server_class(server_address, handler_class)
        print 'Listening on port ' + str(port)
        httpd.serve_forever()


def main():
    if len(sys.argv) == 2:
        trace_file = sys.argv[1]
        run(log_file_path=LOG_FILE + '_RL_' + trace_file)
    else:
        run()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print "Keyboard interrupted."
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
