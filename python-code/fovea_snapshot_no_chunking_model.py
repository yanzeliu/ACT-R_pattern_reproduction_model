import actr
import file_io_util
import math
import random

EXP_WINDOW_WIDTH = 1400
EXP_WINDOW_HEIGHT = 900

CLEAR_CROSS_TIME = 1999
ADD_STIMULUS_TIME = 2000
CLEAR_STIMULUS_TIME = ADD_STIMULUS_TIME + 200
ADD_MASK_TIME = CLEAR_STIMULUS_TIME + 16
CLEAR_MASK_TIME = ADD_MASK_TIME + 1000

VERY_SHORT_STIMULUS_TYPE = "VS"
SHORT_STIMULUS_TYPE = "S"
LONG_STIMULUS_TYPE = "L"

TIME_PER_DISC = 1000

SINGLE_TRIAL_REPEAT_NUM = 1

TOTAL_REFERENCE_NUM = 23
PARAM_INCREASE_STEP = 0.2

PIXELS_PER_VIEWING_ANGLE = 35
LINEAR_FUNC_SLOP = -0.02

FITTING_LEARNING_RATE = 2

actr.load_act_r_model("ACT-R:workspace;short-no-chunking-finsts-fovea-model.lisp")


class disc_chunk:

    def __init__(self, chunk_name, x, y):
        self.chunk_name = chunk_name
        self.x = x
        self.y = y
        self.activation = 0


class ShortFoveaNoChunkingModel:

    def __init__(self, total_reference_count, trial_stim_data):
        # self.current_disc_sequence = None
        # self.current_disc_idx = None
        self.window = None
        self.total_reference_count = total_reference_count
        self.disc_chunks = []
        self.responded_disc_num = 0
        self.mouse_click_timing = []
        self.trial_stim_data = trial_stim_data

        self.clear_cross_time = CLEAR_CROSS_TIME
        self.add_stimulus_time = ADD_STIMULUS_TIME
        self.clear_stimulus_time = self.add_stimulus_time + 50
        self.add_mask_time = self.clear_stimulus_time + 16
        self.clear_mask_time = self.add_mask_time + 1000

        self.type_of_stimulus = "VS"



    # def init_experiment_params(self):
    #     self.current_disc_idx = 0
    #     self.current_disc_sequence = []

    def run_experiment(self, run_in_real_time, type_of_stimulus):

        # self.init_experiment_params()

        actr.reset()

        if not run_in_real_time:
            actr.set_parameter_value(':v', False)
            actr.set_parameter_value(':cmdt', False)

            self.window = actr.open_exp_window("Experiment", visible=False, width=EXP_WINDOW_WIDTH, height=EXP_WINDOW_HEIGHT, x=0, y=0)
        else:
            self.window = actr.open_exp_window("Experiment", width=EXP_WINDOW_WIDTH, height=EXP_WINDOW_HEIGHT, x=0, y=0)

        actr.add_text_to_exp_window(self.window, "X", x=700, y=450, font_size=20)

        actr.add_command("add-stimulus", self.add_stimulus_to_window)
        actr.add_command("add-mask", self.add_mask)
        actr.add_command("create-chunk-tree", self.create_snapshot_chunk_tree)
        actr.add_command("get-next-disc-nnf", self.get_next_disc_chunk_by_distance)
        actr.add_command("get-remain-disc-num", self.get_remain_disc_num)
        actr.add_command("place-response-marker", self.place_response_marker)
        actr.add_command("create-visual-location-chunk", self.create_visual_location_chunk)
        actr.add_command("get-highest-activated-disc", self.get_highest_activated_disc_from_remain_disc_list)
        actr.add_command("update-snapshot-activations", self.assign_reference_count_to_disc_chunks)

        actr.monitor_command("click-mouse", "place-response-marker")
        stim_x = self.trial_stim_data.stim_x
        stim_y = self.trial_stim_data.stim_y

        self.generate_events_timing(type_of_stimulus, len(stim_x))

        actr.schedule_event(self.clear_cross_time, "clear-exp-window", params=[self.window], time_in_ms=True)
        actr.schedule_event(self.add_stimulus_time, "add-stimulus", params=[self.window, stim_x, stim_y],
                            time_in_ms=True)
        actr.schedule_event(self.clear_stimulus_time, "clear-exp-window", params=[self.window], time_in_ms=True)
        actr.schedule_event(self.add_mask_time, "add-mask", params=[self.window], time_in_ms=True)
        actr.schedule_event(self.clear_mask_time, "clear-exp-window", params=[self.window], time_in_ms=True)

        actr.install_device(self.window)
        actr.start_hand_at_mouse()

        actr.set_cursor_location(random.random()*EXP_WINDOW_WIDTH, random.random()*EXP_WINDOW_HEIGHT, 2502)

        if run_in_real_time:
            actr.run(25, True)
        else:
            actr.run(25)

        actr.remove_command("add-stimulus")
        actr.remove_command("add-mask")
        actr.remove_command("create-chunk-tree")
        actr.remove_command("get-next-disc-nnf")
        actr.remove_command("get-remain-disc-num")
        actr.remove_command("place-response-marker")
        actr.remove_command("create-visual-location-chunk")
        actr.remove_command("get-highest-activated-disc")
        actr.remove_command("update-snapshot-activations")

    def add_stimulus_to_window(self, window, stim_x, stim_y):
        for x_coord, y_coord in zip(stim_x, stim_y):
            actr.add_image_to_exp_window(window, "dot", "dot.gif", x=int(x_coord), y=int(y_coord), width=35, height=35)

    def generate_events_timing(self, type_of_stimulus, num_of_discs):
        self.clear_cross_time = CLEAR_CROSS_TIME
        self.add_stimulus_time = ADD_STIMULUS_TIME
        if VERY_SHORT_STIMULUS_TYPE == type_of_stimulus:
            self.clear_stimulus_time = self.add_stimulus_time + 50
        elif SHORT_STIMULUS_TYPE == type_of_stimulus:
            self.clear_stimulus_time = self.add_stimulus_time + 200
        elif LONG_STIMULUS_TYPE == type_of_stimulus:
            self.clear_stimulus_time = self.add_stimulus_time + (1000 * num_of_discs)
        self.add_mask_time = self.clear_stimulus_time + 16
        self.clear_mask_time = self.add_mask_time + 1000

        self.mouse_click_timing.append(self.clear_mask_time)

    def add_mask(self, window):
        actr.add_image_to_exp_window(window, "mask", "mask.gif", x=0, y=0, width=1400, height=900)

    def create_snapshot_chunk_tree(self, visual_location):
        visicon_str = actr.printed_visicon()
        visicon_content_arr = list(filter(lambda x: x.startswith("VISUAL-LOCATION"), visicon_str.split('\n')))
        self.disc_num = len(visicon_content_arr)

        # create disc chunks and store the names of those chunks
        self.disc_chunk_names = []
        for loc_str in visicon_content_arr:
            location_str = loc_str[loc_str.index('(') + 1:loc_str.index(')')].strip()
            coord_arr = location_str.split(' ')
            coord_x = int(coord_arr[0])
            coord_y = int(coord_arr[1])
            tmp_chunk_name = actr.define_chunks(['isa', 'disc', 'type', 'disc-chunk', 'x', coord_x, 'y', coord_y])[0]
            self.disc_chunk_names.append(tmp_chunk_name)
            actr.add_dm_chunks(tmp_chunk_name)
            self.disc_chunks.append(disc_chunk(tmp_chunk_name, coord_x, coord_y))
            # set initial reference count to 0
            actr.set_base_level(tmp_chunk_name, 0)

        # create snapshot root chunk
        root_chunk_slot_params = ['isa', 'snapshot', 'type-tag', 'snapshot']
        for disc_name, slot_idx in zip(self.disc_chunk_names, range(self.disc_num)):
            root_chunk_slot_params.append('slot_' + str(slot_idx + 1))
            root_chunk_slot_params.append(disc_name)
        root_chunk_name = actr.define_chunks(root_chunk_slot_params)[0]
        actr.set_buffer_chunk('imaginal', root_chunk_name)

        # allocate different base-level activations for disc chunks based on their distance to current fovea location
        self.assign_reference_count_to_disc_chunks(visual_location)

    def assign_reference_count_to_disc_chunks(self, current_location):
        fovea_x = actr.chunk_slot_value(current_location, 'screen-x')
        fovea_y = actr.chunk_slot_value(current_location, 'screen-y')

        # calculate shares based on the distance to the fovea location
        proportion_dict = {}
        total_prop = 0
        for disc_chunk_name in self.disc_chunk_names:
            x_coord = actr.chunk_slot_value(disc_chunk_name, 'x')
            y_coord = actr.chunk_slot_value(disc_chunk_name, 'y')
            distance_in_angle = math.sqrt(
                (x_coord - fovea_x) ** 2 + (y_coord - fovea_y) ** 2) / PIXELS_PER_VIEWING_ANGLE

            # calculate the Acuity proportion based on y =  e ^ -(0.13 * x), x is the distance in angle
            cur_prop = math.exp(-0.13 * distance_in_angle)

            # calculate the proportion based on linear function
            # cur_prop = distance_in_angle * LINEAR_FUNC_SLOP + 1

            # calculate the proportion based on log function
            # cur_prop = 1 - math.log(max(distance_in_angle,0.01), 50)

            total_prop += cur_prop
            proportion_dict[disc_chunk_name] = cur_prop
        for disc_chunk_name in self.disc_chunk_names:
            cur_reference_count = actr.sdp(disc_chunk_name, ':reference-count')[0][0]
            # cur_reference_count = 0

            # set based on fixed total
            actr.set_base_level(disc_chunk_name, cur_reference_count + (
                        self.total_reference_count * (proportion_dict[disc_chunk_name] / total_prop)))
            # actr.set_creation_time(disc_chunk_name, -10000000)

            # set based on fixed heightest
            # actr.set_base_level(disc_chunk_name, cur_reference_count + (self.total_reference_count * proportion_dict[disc_chunk_name]) )

            # print(cur_reference_count)
            # print((self.total_reference_count * (proportion_dict[disc_chunk_name] / total_prop)))


    def get_next_disc_chunk_by_distance(self, fixation_location_chunk_name):
        fovea_x = actr.chunk_slot_value(fixation_location_chunk_name, 'screen-x')
        fovea_y = actr.chunk_slot_value(fixation_location_chunk_name, 'screen-y')

        min_distance = math.inf
        min_idx = 0
        for idx, chunk in enumerate(self.disc_chunks):
            tmp_distance = math.sqrt((chunk.x - fovea_x) ** 2 + (chunk.y - fovea_y) ** 2)
            if tmp_distance < min_distance:
                min_distance = tmp_distance
                min_idx = idx
        return self.disc_chunks.pop(min_idx).chunk_name

    def get_highest_activated_disc_from_remain_disc_list(self):
        highest_activation = 0
        highest_idx = 0
        for idx, chunk in enumerate(self.disc_chunks):
            tmp_activation = actr.sdp(chunk.chunk_name, ':activation')[0][0]
            if tmp_activation > highest_activation:
                highest_activation = tmp_activation
                highest_idx = idx
        return self.disc_chunks.pop(highest_idx).chunk_name

    def get_remain_disc_num(self):
        return len(self.disc_chunks)

    def create_visual_location_chunk(self, x, y):
        return actr.define_chunks(['isa', 'visual-location', 'screen-x', x, 'screen-y', y, 'distance', 2502])[0]


    def place_response_marker(self, model,  coords, finger):
        # marker_x = actr.chunk_slot_value(visual_location_chunk_name, 'screen-x')
        # marker_y = actr.chunk_slot_value(visual_location_chunk_name, 'screen-y')
        # response_time = actr.get_time()

        actr.add_text_to_exp_window(self.window, "X", x=coords[0] - 15, y=coords[1] - 15, font_size=40)
        self.responded_disc_num += 1
        self.mouse_click_timing.append(actr.get_time(True))

    def get_pause(self):
        pause_arr = []
        pre_time = -1
        for time in self.mouse_click_timing:
            if pre_time > 0:
                pause_arr.append(time - pre_time)
            pre_time = time
        return pause_arr

    # (sdp disc1:permanent-noise .3)


def get_batch_result(ref_num_param, type_of_stimulus):
    stimulus_map = file_io_util.load_stimulus_from_csv()
    response_data = {}
    pause_data = {}
    for size, stim_data_list in stimulus_map.items():
        for stim_data in stim_data_list:
            for times in range(0, SINGLE_TRIAL_REPEAT_NUM):
                actr_model = ShortFoveaNoChunkingModel(ref_num_param, stim_data)
                actr_model.run_experiment(False, type_of_stimulus)
                responded_disc_num = actr_model.responded_disc_num
                if size in response_data:
                    response_data[size][responded_disc_num] += 1
                else:
                    response_data[size] = [0] * (size + 1)

                # collect pause result
                pause_result = actr_model.get_pause()
                if size in pause_data:
                    pause_data[size].append(pause_result)
                else:
                    pause_data[size] = []

        # normalize the response_num to proportion
        sum_response_num = sum(response_data[size])
        for idx in range(len(response_data[size])):
            response_data[size][idx] = response_data[size][idx] / sum_response_num
        print(response_data[size])

    file_io_util.save_simulation_data(response_data, ref_num_param)
    return response_data,pause_data


def get_loss_func_result(model_data, human_data, display_len=50, stim_size_min=2, stim_size_max=6):
    human_data = human_data[str(display_len)]
    loss = 0
    n = 0
    for stim_size in range(stim_size_min, stim_size_max + 1):
        n += 1
        tmp_human_data = human_data[stim_size]
        if stim_size in model_data.keys():
            tmp_model_data = model_data[stim_size]
        else:
            tmp_model_data = model_data[str(stim_size)]

        # calculate the loss
        if not len(tmp_model_data) == len(tmp_human_data):
            print('input data error! the length of two arrays are not identical.')
            print('length of tmp_model_data: ' + str(len(tmp_model_data)))
            print('length of tmp_human_data: ' + str(len(tmp_human_data)))
            return -1

        for tmp_human_proportion, tmp_model_proportion in zip(tmp_human_data, tmp_model_data):
            loss += abs(tmp_human_proportion - tmp_model_proportion)
            # return loss / n
        return loss


def iterate_params_by_step(starting_param, step=0.2, iterations=20, type_of_stimulus=VERY_SHORT_STIMULUS_TYPE):
    human_data = file_io_util.load_human_data_from_csv()

    cur_param = starting_param
    for i in range(iterations):
        model_data, pause_data = get_batch_result(cur_param, type_of_stimulus)
        cur_loss = get_loss_func_result(model_data, human_data)
        print(f"Iteration {i + 1}: Cost {cur_loss}, Reference_Count_Param {cur_param}")
        cur_param += step

    file_io_util.save_pause_data(pause_data)
    return [cur_param, cur_loss]


def test_run(type_of_stimulus):
    stimulus_map = file_io_util.load_stimulus_from_csv()
    trial_stim_data = stimulus_map.get(9)[10]

    test = ShortFoveaNoChunkingModel(TOTAL_REFERENCE_NUM, trial_stim_data)
    test.run_experiment(True, type_of_stimulus)
    print(test.responded_disc_num)
    print(test.get_pause())


def main():
    # test_run(VERY_SHORT_STIMULUS_TYPE)
    test_run(SHORT_STIMULUS_TYPE)
    # test_run(LONG_STIMULUS_TYPE)


    # iterate_params_by_step(5, iterations=30, step=0.5, type_of_stimulus=VERY_SHORT_STIMULUS_TYPE)
    # iterate_params_by_step(5, iterations=30, step=0.5, type_of_stimulus=SHORT_STIMULUS_TYPE)


if __name__ == '__main__':
    main()
