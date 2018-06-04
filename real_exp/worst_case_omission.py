import os
import numpy as np
import matplotlib.pyplot as plt

RESULTS_FOLDER = './results/'
SCHEMES = ['robustMPC', 'RL']
TESTS = ['Verizon_LTE', 'International_Link', 'Stanford_Visitor']
BITS_IN_BYTE = 8.0
MILLISEC_IN_SEC = 1000.0
M_IN_B = 1000000.0
REBUF_PENALTY = 4.3

# Compute the worst two values, then find the corresponding QoE for the file
def find_worst_qoe(bit_rate, rebuf_time):
    bitrate_diff_sum = 0
    first_pos = 0
    second_pos = 1
    for i in range(len(bit_rate)-1):
        for j in range(i+1, len(bit_rate)-1):
            quality_diff = abs(bit_rate[i] - bit_rate[j])
            if quality_diff > bitrate_diff_sum:
                bitrate_diff_sum = quality_diff
                first_pos = i
                second_pos = j
    bitrate_diff_sum = bitrate_diff_sum / 1000.0
    bitrate_sum = (bit_rate[first_pos] + bit_rate[second_pos]) / 1000.0
    rebuffer_sum = rebuf_time[first_pos] + rebuf_time[second_pos]
    qoe_val = bitrate_sum - REBUF_PENALTY * rebuffer_sum - bitrate_diff_sum
    qoe_val_normalized = qoe_val / 2
    return (qoe_val, qoe_val_normalized)

# Compute the worst two values, then find the corresponding QoE for the file
def find_best_qoe(bit_rate, rebuffer_time):
    bitrate_diff_sum = float('inf')
    for i in range(len(bit_rate)-1):
        for j in range(i+1, len(bit_rate)-1):
            quality_diff = abs(bit_rate[i] - bit_rate[j])
            if quality_diff < bitrate_diff_sum:
                bitrate_diff_sum = quality_diff
                first_pos = i
                second_pos = j
    bitrate_diff_sum = bitrate_diff_sum / 1000.0
    bitrate_sum = (bit_rate[i] + bit_rate[j]) / 1000.0
    rebuffer_sum = rebuf_time[i] + rebuf_time[j]
    qoe_val = bitrate_sum - REBUF_PENALTY * rebuffer_sum - bitrate_diff_sum
    qoe_val_normalized = qoe_val / 2
    return (qoe_val, qoe_val_normalized)

# Note that we are only interested in QoE lin, and so will only compute using
# that metric.
# QoE = sum(q(R_n)) - u*sum(T_n) - sum(q(R_n) - q(R_n+1))
def main():

    colorsList = ['orange', 'blue', 'red']
    time_all = {}
    bit_rate_all = {}
    rebuf_time_all = {}
    bw_all = {}
    raw_reward_all = {}
    qoe_all = {}
    qoe_vals = {}
    colors = {}
    i = 0
    for scheme in SCHEMES:
        colors[scheme] = colorsList[i]
        time_all[scheme] = {}
        raw_reward_all[scheme] = {}
        bit_rate_all[scheme] = {}
        rebuf_time_all[scheme] = {}
        bw_all[scheme] = {}
        qoe_all[scheme] = {}
        qoe_vals[scheme] = {}
        i += 1
        for test in TESTS:
            time_all[scheme][test] = {}
            raw_reward_all[scheme][test] = {}
            bit_rate_all[scheme][test] = {}
            rebuf_time_all[scheme][test] = {}
            bw_all[scheme][test] = {}
            qoe_all[scheme][test] = {}
            qoe_vals[scheme][test] = []

    log_files = os.listdir(RESULTS_FOLDER)
    for log_file in log_files:

        time_ms = []
        bit_rate = []
        rebuf_time = []
        bw = []
        reward = []

        with open(RESULTS_FOLDER + log_file, 'rb') as f:
            for line in f:
                parse = line.split()
                if len(parse) <= 1:
                    # Indicates EoF
                    break
                time_ms.append(float(parse[0]))
                bit_rate.append(int(parse[1]))
                rebuf_time.append(float(parse[3]))
                bw.append(float(parse[4]) / float(parse[5]) * BITS_IN_BYTE * MILLISEC_IN_SEC / M_IN_B)
                reward.append(float(parse[6]))

        # Compute QoE metric
        # QoE = sum(q(R_n)) - u*sum(T_n) - sum(q(R_n) - q(R_n+1))
        '''
        bitrate_sum = np.sum(bit_rate) / 1000.0
        rebuffer_sum = np.sum(rebuf_time)
        bitrate_diff_sum = 0
        for j in range(len(bit_rate)-1):
            bitrate_diff_sum += abs(bit_rate[j] - bit_rate[j+1])
        bitrate_diff_sum = bitrate_diff_sum / 1000.0

        qoe_val = bitrate_sum - REBUF_PENALTY * rebuffer_sum - bitrate_diff_sum
        qoe_val_normalized = qoe_val / len(bit_rate)
        '''

        (qoe_val, qoe_val_normalized) = find_worst_qoe(bit_rate, rebuf_time)

        time_ms = np.array(time_ms)
        time_ms -= time_ms[0]

        for test in TESTS:
            for scheme in SCHEMES:
                if test in log_file and scheme in log_file:
                    log_file_id = log_file[len(str(test) + '_log_' + str(scheme) + '_'):]
                    time_all[scheme][test][log_file_id] = time_ms
                    bit_rate_all[scheme][test][log_file_id] = bit_rate
                    rebuf_time_all[scheme][test][log_file_id] = rebuf_time
                    bw_all[scheme][test][log_file_id] = bw
                    raw_reward_all[scheme][test][log_file_id] = reward
                    qoe_vals[scheme][test].append(qoe_val_normalized)
                    qoe_all[scheme][test][log_file_id] = \
                            (qoe_val_normalized, qoe_val)
                            #(qoe_val_normalized, qoe_val, bitrate_sum, rebuffer_sum, bitrate_diff_sum)
                    print "QoE for Scheme: ", scheme + " " + str(log_file_id)
                    '''
                    print "Bitrate sum: ", bitrate_sum
                    print "Rebuffer sum: ", rebuffer_sum
                    print "Bitrate diff sum: ", bitrate_diff_sum
                    '''
                    print "Computed QoE metric of: ", qoe_val
                    print "Computed normalized QoE metric of: ", qoe_val_normalized
                    print "\n"
                    break

    qoe_results = {}
    qoe_stddev = {}
    for scheme in SCHEMES:
        qoe_results[scheme] = []
        qoe_stddev[scheme] = []
        for test in TESTS:
            print "QoE vals: ", qoe_vals[scheme][test]
            qoe_results[scheme].append(np.mean(qoe_vals[scheme][test]))
            qoe_stddev[scheme].append(np.std(qoe_vals[scheme][test]))

    X = np.arange(len(TESTS))
    x_offset = 0
    plots_to_label = ()
    label_names = ()
    for scheme in SCHEMES:
        plot = plt.bar(X + x_offset, qoe_results[scheme], yerr=qoe_stddev[scheme], label = scheme, capsize=5, width=0.25, color=colors[scheme])
        plots_to_label = plots_to_label + (plot[0],)
        label_names = label_names + (scheme,)
        x_offset += 0.25
        print "SCHEME: ", scheme
        print qoe_results[scheme]
        print qoe_stddev[scheme]
        print len(X)
    # We assume the tests are in the correct order...
    x_tick_labels = tuple(TESTS)
    n_tests = len(TESTS)
    offset = 0.25
    ind = np.arange(offset, n_tests + offset)
    plt.xticks(ind, x_tick_labels)
    plt.legend(plots_to_label, label_names)
    plt.show()


if __name__ == '__main__':
    main()
