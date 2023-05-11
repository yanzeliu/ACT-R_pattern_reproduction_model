import csv
from os import walk
import json
from stimulus_util import stimulus_data


def load_stimulus_from_csv():
    # read filenames
    folder_name = './stimulus_data'
    filenames = next(walk(folder_name), (None, None, []))[2]

    stimulus_map = dict()
    for name in filenames:
        stimulus_list = []
        with open(folder_name + '/' + name, newline='') as csvfile:
            spamreader = csv.reader(csvfile, delimiter=',', quotechar='|')
            for row in spamreader:
                if row[0].startswith('x'):
                    y_start = row.index('yStim_1')
                else:
                    stimulus_list.append(stimulus_data(row[:y_start], row[y_start:]))
        stimulus_map[int(name[0])] = stimulus_list
    return stimulus_map

def load_human_data_from_csv():
    folder_name = './human_response_data'
    subfolder_names = next(walk(folder_name), (None, None, []))[1]
    human_prop_data = {}
    for subfolder in subfolder_names:
        filenames = next(walk(folder_name + '/' + subfolder), (None, None, []))[2]
        human_prop_data_cell = {}
        for file in filenames:
            if not file.endswith('csv'):
                continue
            with open(folder_name + '/' + subfolder + '/' + file, newline='') as csvfile:
                spamreader = csv.reader(csvfile, delimiter=',', quotechar='|')
                proportion_arr = []
                stim_len = 0
                for row, contant in enumerate(spamreader):
                    if row == 0:
                        continue
                    elif row == 1:
                        proportion_arr = [0] * (int(contant[1]) + 1)
                        stim_len = int(contant[1])
                    proportion_arr[int(contant[0])] = float(contant[4])
            human_prop_data_cell[stim_len] = proportion_arr
        human_prop_data[subfolder] = human_prop_data_cell
    return human_prop_data

def save_simulation_data(data_dict, total_reference_param):
    with open('./simulation_data/percentage_data/data_'+ str(round(total_reference_param,2)) + '.json', 'w') as fp:
        json.dump(data_dict, fp)

def load_simulation_data(param_val):
    with open('./simulation_data/percentage_data/data_' + str(param_val) + '.json', 'r') as fp:
        data = json.load(fp)
    # print(data)
    return data

def save_pause_data(pause_list: dict):
    for key in pause_list.keys():
        pause_arr = pause_list[key]
        with open('./simulation_data/pause_data/pause_' + str(key) + '.csv', 'w') as f:
            write = csv.writer(f)
            write.writerows(pause_arr)
    # with open('./simulation_data/pause_data/pause.csv', 'w') as f:
    #     write = csv.writer(f)
    #     # write.writerow(Details)
    #     write.writerows(pause_list)

def test():
    load_human_data_from_csv()
    # load_stimulus_from_csv(9)

if __name__ == '__main__':
    test()
