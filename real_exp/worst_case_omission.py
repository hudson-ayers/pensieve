import os
import numpy as np
import matplotlib.pyplot as plt
import random

RESULTS_FOLDER = './results/'
SCHEMES = ['robustMPC', 'RL']
TESTS = ['Verizon_LTE', 'International_Link', 'Stanford_Visitor']
REBUF_PENALTY = 4.3
DEFAULT_SAMPLE_SIZE = 20
NUM_SAMPLES = 20

def compute_true_qoe(bit_rate, rebuf_time):
    # TODO: Figure out whether this is correct, or if bitrate_diff_sum should
    # be initalized to 0
    #bitrate_diff_sum = bit_rate[0]
    bitrate_diff_sum = 0
    for j in range(len(bit_rate)-1):
        bitrate_diff_sum += abs(bit_rate[j] - bit_rate[j+1])
    bitrate_diff_sum = bitrate_diff_sum / 1000.0

    bitrate_sum = np.sum(bit_rate) / 1000.0
    rebuffer_sum = np.sum(rebuf_time)

    qoe_val = bitrate_sum - REBUF_PENALTY * rebuffer_sum - bitrate_diff_sum
    qoe_val_normalized = qoe_val / len(bit_rate)
    return qoe_val_normalized

def find_random_qoe(bit_rate, rebuf_time, sample_size):
    # Values here should be distinct
    positions = random.sample(range(0, len(bit_rate)), sample_size)
    positions.sort()
    bitrate_diff_sum = 0
    for i in range(len(positions)-1):
        bitrate_diff_sum += abs(bit_rate[positions[i]] - bit_rate[positions[i+1]])
    bitrate_diff_sum = bitrate_diff_sum / 1000.0

    bitrate_sum = 0
    rebuffer_sum = 0
    for i in positions:
        bitrate_sum += bit_rate[i]
        rebuffer_sum += rebuf_time[i]
    bitrate_sum = bitrate_sum / 1000.0

    qoe_val = bitrate_sum - REBUF_PENALTY * rebuffer_sum - bitrate_diff_sum
    qoe_val_normalized = qoe_val / len(positions)
    return qoe_val_normalized

def find_min_sample_size():
    min_line_count = float('inf')
    log_files = os.listdir(RESULTS_FOLDER)
    for log_file in log_files:
        line_count = 0
        with open(RESULTS_FOLDER + log_file, 'rb') as f:
            for line in f:
                parse = line.split()
                if len(parse) <= 1:
                    break
                line_count += 1
        min_line_count = min(line_count, min_line_count)
        print "MIN LINE COUNT: ", min_line_count
    return min_line_count

def get_random_samples(bit_rate, rebuf_time, sample_size, num_samples):
    qoe_values = []
    for i in range(num_samples):
        qoe_values.append(find_random_qoe(bit_rate, rebuf_time, sample_size))
    return qoe_values

def plot_results(true_vals, true_stddevs, best_vals, best_stddevs, worst_vals, worst_stddevs, colors):
    X = np.arange(len(TESTS))
    x_offset = 0
    plots_to_label = ()
    label_names = ()

    for scheme in SCHEMES:
        name = scheme + " true value"
        plot = plt.bar(X + x_offset, true_vals[scheme], yerr=true_stddevs[scheme], label=name, capsize=5, width=0.125, color=colors[scheme][0])
        plots_to_label = plots_to_label + (plot[0],)
        label_names = label_names + (name,)
        x_offset += 0.125

        name = scheme + " best run"
        plot = plt.bar(X + x_offset, best_vals[scheme], yerr=best_stddevs[scheme], label=name, capsize=5, width=0.125, color=colors[scheme][1])
        plots_to_label = plots_to_label + (plot[0],)
        label_names = label_names + (name,)
        x_offset += 0.125

        name = scheme + " worst run"
        plot = plt.bar(X + x_offset, worst_vals[scheme], yerr=worst_stddevs[scheme], label=name, capsize=5, width=0.125, color=colors[scheme][2])
        plots_to_label = plots_to_label + (plot[0],)
        label_names = label_names + (name,)
        x_offset += 0.125

        x_offset += 0.0625

    # We assume the tests are in the correct order...
    x_tick_labels = tuple(TESTS)
    n_tests = len(TESTS)
    offset = 0.30
    ind = np.arange(offset, n_tests + offset)
    plt.xticks(ind, x_tick_labels)
    plt.legend(plots_to_label, label_names)
    plt.show()


# Note that we are only interested in QoE lin, and so will only compute using
# that metric.
# QoE = sum(q(R_n)) - u*sum(T_n) - sum(q(R_n) - q(R_n+1))
def main():

    colorsList = [['xkcd:sky blue', 'xkcd:royal blue', 'xkcd:cerulean'],
                  ['xkcd:light red', 'xkcd:rust', 'xkcd:crimson', 'xkcd:scarlet']]
    raw_reward_all = {}
    qoe_vals = {}
    qoe_samples = {}
    colors = {}
    i = 0
    for scheme in SCHEMES:
        colors[scheme] = colorsList[i]
        raw_reward_all[scheme] = {}
        qoe_vals[scheme] = {}
        qoe_samples[scheme] = {}
        i += 1
        for test in TESTS:
            raw_reward_all[scheme][test] = {}
            qoe_vals[scheme][test] = []
            qoe_samples[scheme][test] = []

    sample_size = find_min_sample_size()
    log_files = os.listdir(RESULTS_FOLDER)
    for log_file in log_files:

        bit_rate = []
        rebuf_time = []
        reward = []

        with open(RESULTS_FOLDER + log_file, 'rb') as f:
            for line in f:
                parse = line.split()
                if len(parse) <= 1:
                    # Indicates EoF
                    break
                bit_rate.append(int(parse[1]))
                rebuf_time.append(float(parse[3]))
                reward.append(float(parse[6]))

        qoe_val_normalized = compute_true_qoe(bit_rate, rebuf_time)
        qoe_random_samples = get_random_samples(bit_rate, rebuf_time, sample_size, NUM_SAMPLES)

        for test in TESTS:
            for scheme in SCHEMES:
                if test in log_file and scheme in log_file:
                    log_file_id = log_file[len(str(test) + '_log_' + str(scheme) + '_'):]
                    raw_reward_all[scheme][test][log_file_id] = reward
                    qoe_vals[scheme][test].append(qoe_val_normalized)
                    qoe_samples[scheme][test].append(qoe_random_samples)
                    break

    true_vals = {}
    true_stddevs = {}
    best_vals = {}
    best_stddevs = {}
    worst_vals = {}
    worst_stddevs = {}
    for scheme in SCHEMES:
        true_vals[scheme] = []
        true_stddevs[scheme] = []
        best_vals[scheme] = []
        best_stddevs[scheme] = []
        worst_vals[scheme] = []
        worst_stddevs[scheme] = []
        for test in TESTS:
            true_mean = np.mean(qoe_vals[scheme][test])
            true_stddev = np.std(qoe_vals[scheme][test])
            best_mean = 0
            best_stddev = 0
            worst_mean = float('inf')
            worst_stddev = 0
            for i in range(NUM_SAMPLES):
                qoe_arr = []
                for j in range(len(qoe_samples[scheme][test])):
                    qoe_arr.append(qoe_samples[scheme][test][j][i])
                mean = np.mean(qoe_arr)
                stddev = np.std(qoe_arr)
                if mean > best_mean:
                    best_mean = mean
                    best_stddev = stddev
                if mean < worst_mean:
                    worst_mean = mean
                    worst_stddev = stddev
            true_vals[scheme].append(true_mean)
            true_stddevs[scheme].append(true_stddev)
            best_vals[scheme].append(best_mean)
            best_stddevs[scheme].append(best_stddev)
            worst_vals[scheme].append(worst_mean)
            worst_stddevs[scheme].append(worst_stddev)

    plot_results(true_vals, true_stddevs, best_vals, best_stddevs, worst_vals, worst_stddevs, colors)

if __name__ == '__main__':
    main()
