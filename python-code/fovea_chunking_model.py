import actr
import file_io_util
import math
import random
import pattern_util
import numpy as np

import stimulus_util

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

# TIME_PER_DISC = 1000
TIME_PER_DISC = 200

SINGLE_TRIAL_REPEAT_NUM = 5

TOTAL_REFERENCE_NUM = 10
PARAM_INCREASE_STEP = 0.2

PIXELS_PER_VIEWING_ANGLE = 35
LINEAR_FUNC_SLOP = -0.02

FITTING_LEARNING_RATE = 2

actr.load_act_r_model("ACT-R:workspace;long-chunking-model.lisp")


class disc_chunk:

    def __init__(self, chunk_name, x, y):
        self.chunk_name = chunk_name
        self.x = x
        self.y = y
        self.activation = 0


class LongFoveaChunkingModel:

    def __init__(self, total_reference_count, trial_stim_data):
        self.root_chunk_name = None
        self.pattern_chunk_name_list = []
        self.window = None
        self.total_reference_count = total_reference_count
        self.disc_chunks = []
        self.responded_disc_num = 0
        self.mouse_click_timing = []
        self.trial_stim_data = trial_stim_data
        self.explored_stim_idx = []
        self.chunked_stim_idx = np.array([])
        self.cur_slot_idx = 0
        self.cur_tar_chunk_name = None
        self.cur_in_chunk_slot_idx = 1

        self.clear_cross_time = CLEAR_CROSS_TIME
        self.add_stimulus_time = ADD_STIMULUS_TIME
        self.clear_stimulus_time = self.add_stimulus_time + 50
        self.add_mask_time = self.clear_stimulus_time + 16
        self.clear_mask_time = self.add_mask_time + 1000

        self.type_of_stimulus = "VS"

        self.cur_group_idx = 1




    # def init_experiment_params(self):
    #     self.current_disc_idx = 0
    #     self.current_disc_sequence = []

    def run_experiment(self, run_in_real_time, type_of_stimulus):

        # self.init_experiment_params()

        actr.reset()

        if not run_in_real_time:
            actr.set_parameter_value(':v', False)
            actr.set_parameter_value(':cmdt', False)

            self.window = actr.open_exp_window("Experiment", visible=False, width=EXP_WINDOW_WIDTH,
                                               height=EXP_WINDOW_HEIGHT, x=0, y=0)
        else:
            self.window = actr.open_exp_window("Experiment", width=EXP_WINDOW_WIDTH, height=EXP_WINDOW_HEIGHT, x=0, y=0)

        actr.add_text_to_exp_window(self.window, "X", x=700, y=450, font_size=20)

        actr.add_command("add-stimulus", self.add_stimulus_to_window)
        actr.add_command("add-mask", self.add_mask)
        actr.add_command("take-snapshot", self.create_snapshot_chunk_tree)
        actr.add_command("get-salient-pattern", self.get_salient_pattern_from_explored_stimmulus)
        actr.add_command("split-non-pattern-disc", self.get_group_from_non_pattern_disc)
        actr.add_command("check-if-chunk-slot-is-empty", self.check_chunk_slot_is_empty)
        actr.add_command("get-next-group-slot-name", self.get_next_group_slot_name)
        actr.add_command("reset-root-slot-index", self.reset_current_root_slot_index)
        actr.add_command("create-visual-location-chunk", self.create_visual_location_chunk)
        actr.add_command("get-next-in-group-slot", self.get_next_disc_slot_name_in_group)
        actr.add_command("get-next-group-slot-name-for-response", self.get_next_group_slot_name_during_response)
        actr.add_command("place-response-marker", self.place_response_marker)

        actr.add_command("get-highest-activated-disc", self.get_highest_activated_disc_from_remain_disc_list)
        actr.add_command("update-snapshot-activations", self.assign_reference_count_to_disc_chunks)
        actr.add_command("get-next-disc-slot-name", self.get_next_slot_name)
        actr.add_command("get-remain-ingroup-disc", self.get_remain_slot_num)



        actr.monitor_command("click-mouse", "place-response-marker")
        stim_x = self.trial_stim_data.stim_x
        stim_y = self.trial_stim_data.stim_y

        self.get_sailent_patterns_from_stimulus()

        self.generate_events_timing(type_of_stimulus, len(stim_x))

        actr.schedule_event(self.clear_cross_time, "clear-exp-window", params=[self.window], time_in_ms=True)
        actr.schedule_event(self.add_stimulus_time, "add-stimulus", params=[self.window, stim_x, stim_y],
                            time_in_ms=True)
        actr.schedule_event(self.clear_stimulus_time, "clear-exp-window", params=[self.window], time_in_ms=True)
        actr.schedule_event(self.add_mask_time, "add-mask", params=[self.window], time_in_ms=True)
        actr.schedule_event(self.clear_mask_time, "clear-exp-window", params=[self.window], time_in_ms=True)

        actr.install_device(self.window)
        actr.start_hand_at_mouse()

        actr.set_cursor_location(random.random() * EXP_WINDOW_WIDTH, random.random() * EXP_WINDOW_HEIGHT, 2502)

        if run_in_real_time:
            actr.run(40, True)
        else:
            actr.run(40)

        actr.remove_command("add-stimulus")
        actr.remove_command("add-mask")
        actr.remove_command("take-snapshot")
        actr.remove_command("get-salient-pattern")
        actr.remove_command("split-non-pattern-disc")
        actr.remove_command("check-if-chunk-slot-is-empty")
        actr.remove_command("get-next-group-slot-name")
        actr.remove_command("reset-root-slot-index")
        actr.remove_command("create-visual-location-chunk")
        actr.remove_command("get-next-in-group-slot")
        actr.remove_command("get-next-group-slot-name-for-response")
        actr.remove_command("place-response-marker")

        actr.remove_command("get-highest-activated-disc")
        actr.remove_command("update-snapshot-activations")
        actr.remove_command("get-next-disc-slot-name")
        actr.remove_command("get-remain-ingroup-disc")

    def add_stimulus_to_window(self, window, stim_x, stim_y):
        for x_coord, y_coord in zip(stim_x, stim_y):
            actr.add_image_to_exp_window(window, "dot", "dot.gif", x=int(x_coord), y=int(y_coord), width=35, height=35)

    def generate_events_timing(self, type_of_stimulus, num_of_discs):
        self.clear_cross_time = CLEAR_CROSS_TIME
        self.add_stimulus_time = ADD_STIMULUS_TIME
        if type_of_stimulus == "VS":
            self.clear_stimulus_time = self.add_stimulus_time + 50
        elif type_of_stimulus == "S":
            self.clear_stimulus_time = self.add_stimulus_time + 200
        elif type_of_stimulus == "L":
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
            tmp_chunk_name = actr.define_chunks(['isa', 'disc', 'type-tag', 'disc-chunk', 'x', coord_x, 'y', coord_y])[
                0]
            self.disc_chunk_names.append(tmp_chunk_name)
            actr.add_dm_chunks(tmp_chunk_name)
            self.disc_chunks.append(disc_chunk(tmp_chunk_name, coord_x, coord_y))
            # set initial reference count to 0
            actr.set_base_level(tmp_chunk_name, 0)

        # create snapshot root chunk
        root_chunk_slot_params = ['isa', 'root', 'type-tag', 'snapshot']
        for disc_name, slot_idx in zip(self.disc_chunk_names, range(self.disc_num)):
            root_chunk_slot_params.append('slot' + str(slot_idx + 1))
            root_chunk_slot_params.append(disc_name)
        root_chunk_name = actr.define_chunks(root_chunk_slot_params)[0]
        actr.set_buffer_chunk('imaginal', root_chunk_name)

        # allocate different base-level activations for disc chunks based on their distance to current fovea location
        self.assign_reference_count_to_disc_chunks(visual_location)

    def reset_browsing_status(self):
        self.explored_stim_idx = []
        self.chunked_stim_idx = np.array([])
        self.loc_on_visicon = np.zeros([len(self.trial_stim_data.stim_x), 2])
        self.pattern_chunk_name_list = []

    def get_salient_pattern_from_explored_stimmulus(self, visual_location):
        stim_visicon_x = actr.chunk_slot_value(visual_location, 'screen-x')
        stim_visicon_y = actr.chunk_slot_value(visual_location, 'screen-y')
        visicon_loc = np.array((stim_visicon_x, stim_visicon_y)).astype(np.float64)

        stim_x = np.array(self.trial_stim_data.stim_x).astype(np.float64)
        stim_y = np.array(self.trial_stim_data.stim_y).astype(np.float64)
        stim_points = np.column_stack((stim_x, stim_y))

        nearest_stim_idx = np.argmin(np.linalg.norm(stim_points - visicon_loc, axis=1))
        if nearest_stim_idx in self.explored_stim_idx:
            return 'not-found'

        self.explored_stim_idx.append(nearest_stim_idx)
        self.trial_stim_data.loc_on_visicon[nearest_stim_idx, :] = visicon_loc
        explored_stim_idx = np.array(self.explored_stim_idx)

        # get the first pattern tuple for the disc
        pattern_tuple = self.trial_stim_data.pattern_tuple_for_disc[nearest_stim_idx][0]
        if pattern_tuple[0] != stimulus_util.GROUP_TAG:
            pattern_idx = pattern_tuple[1]
            # check whether pattern_idx is subset of explored_stim_idx
            if np.all(np.in1d(pattern_idx, explored_stim_idx)):
                pattern_params = ['isa']
                if pattern_tuple[0] == stimulus_util.TRIANGLE_TAG:
                    pattern_params.extend(['triangle', 'type-tag', 'triangle'])
                elif pattern_tuple[0] == stimulus_util.SQUARE_TAG:
                    pattern_params.extend(['square', 'type-tag', 'square'])

                slot_name_idx = 1
                for idx in pattern_idx:
                    pattern_params.append('x' + str(slot_name_idx))
                    pattern_params.append(str(self.trial_stim_data.loc_on_visicon[idx, 0]))
                    # pattern_params.append(str(stim_x[idx]))
                    pattern_params.append('y' + str(slot_name_idx))
                    # pattern_params.append(str(stim_y[idx]))
                    pattern_params.append(str(self.trial_stim_data.loc_on_visicon[idx, 1]))
                    slot_name_idx += 1

                pattern_chunk_name = actr.define_chunks(pattern_params)[0]
                actr.set_buffer_chunk('imaginal', pattern_chunk_name)
                self.pattern_chunk_name_list.append(pattern_chunk_name)
                self.chunked_stim_idx = np.append(self.chunked_stim_idx, pattern_idx)
                return 'found'
        return 'not-found'

    def get_group_from_non_pattern_disc(self):
        explored_stim_idx = np.array(self.explored_stim_idx)
        unchunked_disc_idx = np.setdiff1d(explored_stim_idx, self.chunked_stim_idx)
        if len(unchunked_disc_idx) == 0:
            return 'not-found'
        unchunked_disc_idx = unchunked_disc_idx[np.argsort(
            [-len(self.trial_stim_data.pattern_tuple_for_disc[idx][0][1]) for idx in unchunked_disc_idx])]
        tar_disc_idx = unchunked_disc_idx[0]
        pattern_tuple = self.trial_stim_data.pattern_tuple_for_disc[tar_disc_idx][0]
        pattern_idx = pattern_tuple[1]
        pattern_params = ['isa', 'disc-group', 'type-tag', 'disc-group', 'size', str(len(pattern_idx))]
        for idx, disc_idx in enumerate(pattern_idx):
            tmp_visicon_loc = self.trial_stim_data.loc_on_visicon[disc_idx, :]
            tmp_tar_x = tmp_visicon_loc[0]
            tmp_tar_y = tmp_visicon_loc[1]
            for disc_chunk in self.disc_chunks:
                if disc_chunk.x == tmp_tar_x and disc_chunk.y == tmp_tar_y:
                    pattern_params.append('disc' + str(idx + 1))
                    pattern_params.append(disc_chunk.chunk_name)
                    cur_reference_count = actr.sdp(disc_chunk.chunk_name, ':reference-count')[0][0]
                    actr.set_base_level(disc_chunk.chunk_name, cur_reference_count + 1)
        pattern_chunk_name = actr.define_chunks(pattern_params)[0]
        actr.set_buffer_chunk('imaginal', pattern_chunk_name)
        self.pattern_chunk_name_list.append(pattern_chunk_name)
        self.chunked_stim_idx = np.append(self.chunked_stim_idx, pattern_idx)
        return 'found'

    def check_chunk_slot_is_empty(self, chunk_name, slot_name):
        slot_value = actr.chunk_slot_value(chunk_name, slot_name)
        if None == slot_value:
            return True
        else:
            return False

    def reset_current_root_slot_index(self):
        self.cur_slot_idx = 0
        # print('root slot reset to 0')

    def get_next_group_slot_name(self):
        next_group_name = 'slot' + str(self.cur_slot_idx + 1)
        self.cur_slot_idx = (self.cur_slot_idx + 1) % len(self.pattern_chunk_name_list)
        return next_group_name

    def get_next_group_slot_name_during_response(self):
        if self.cur_slot_idx == len(self.pattern_chunk_name_list):
            return 'response-finished'
        next_group_name = 'slot' + str(self.cur_slot_idx + 1)
        self.cur_slot_idx = (self.cur_slot_idx + 1)
        print( next_group_name)
        return next_group_name

    def create_visual_location_chunk(self, x, y):
        return actr.define_chunks(['isa', 'visual-location', 'screen-x', x, 'screen-y', y, 'distance', 2502])[0]

    def get_next_disc_slot_name_in_group(self, chunk_name):
        if self.cur_tar_chunk_name != chunk_name:
            self.cur_in_chunk_slot_idx = 1
            self.cur_tar_chunk_name = chunk_name

        next_slot_name = 'disc' + str(self.cur_in_chunk_slot_idx)
        slot_val = actr.chunk_slot_value(chunk_name, next_slot_name)
        print((chunk_name, next_slot_name, slot_val))
        if None == slot_val:
            self.cur_in_chunk_slot_idx = 1
            return 'chunk-rehearsal-finish'
        else:
            self.cur_in_chunk_slot_idx += 1
            return next_slot_name

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
            # cur_prop = math.exp(-0.13 * distance_in_angle)

            # calculate the proportion based on linear function
            # cur_prop = distance_in_angle * LINEAR_FUNC_SLOP + 1

            # calculate the proportion based on log function
            cur_prop = 1 - math.log(max(distance_in_angle, 0.01), 50)

            total_prop += cur_prop
            proportion_dict[disc_chunk_name] = cur_prop
        for disc_chunk_name in self.disc_chunk_names:
            cur_reference_count = actr.sdp(disc_chunk_name, ':reference-count')[0][0]
            # cur_reference_count = 0

            # set based on fixed total
            actr.set_base_level(disc_chunk_name, cur_reference_count + (
                    self.total_reference_count * (proportion_dict[disc_chunk_name] / total_prop)))

    def create_square_pattern_chunk(self, vertex_list):
        print(vertex_list)
        square_chunk_params = ['isa', 'square', 'type-tag', 'square']
        for idx, disc_name in enumerate(vertex_list):
            square_chunk_params.append('vertex_' + str(idx + 1))
            square_chunk_params.append(disc_name)
        square_chunk_name = actr.define_chunks(square_chunk_params)[0]
        actr.add_dm_chunks(square_chunk_name)
        return square_chunk_name

    def create_arbitrary_group_chunk(self, disc_list):
        print(disc_list)
        if len(disc_list) == 1:
            group_chunk_name = disc_list[0]
        elif len(disc_list) == 0:
            group_chunk_name = None
        else:
            chunk_params = ['isa', 'arbitrary-group', 'type-tag', 'arbitrary-group', 'size', len(disc_list)]
            for idx, disc_name in enumerate(disc_list):
                chunk_params.append('vertex_' + str(idx + 1))
                chunk_params.append(disc_name)
            group_chunk_name = actr.define_chunks(chunk_params)[0]
            actr.add_dm_chunks(group_chunk_name)
        return group_chunk_name

    def init_sub_group_slot_name_list(self, subgroup_chunk_name):
        type_tag = actr.chunk_slot_value(subgroup_chunk_name, 'type-tag')
        if 'square' == type_tag.lower():
            self.slot_list = ['vertex_1', 'vertex_2', 'vertex_3', 'vertex_4']
        elif 'triangle' == type_tag.lower():
            self.slot_list = ['vertex_1', 'vertex_2', 'vertex_3']
        elif 'arbitrary-group' == type_tag.lower():
            group_length = actr.chunk_slot_value(subgroup_chunk_name, 'size')
            self.slot_list = ['vertex_1', 'vertex_2', 'vertex_3', 'vertex_4', 'vertex_5'][:group_length]
        # match type_tag.lower():
        #     case 'square':
        #         self.slot_list = ['vertex_1', 'vertex_2', 'vertex_3', 'vertex_4']
        #     case 'triangle':
        #         self.slot_list = ['vertex_1', 'vertex_2', 'vertex_3']
        #     case 'arbitrary-group':
        #         group_length = actr.chunk_slot_value(subgroup_chunk_name, 'size')
        #         self.slot_list = ['vertex_1', 'vertex_2', 'vertex_3', 'vertex_4', 'vertex_5'][:group_length]

    def get_sailent_patterns_from_stimulus(self):
        print(self.trial_stim_data.pattern_map)

    def get_next_slot_name(self):
        return self.slot_list.pop(0) if len(self.slot_list) > 0 else 'empty'

    def get_remain_slot_num(self):
        return len(self.slot_list)

    def get_next_disc_slot_name(self):
        next_slot_name = 'vertex_' + str(self.cur_slot_idx)
        self.cur_slot_idx += 1
        return next_slot_name

    def get_highest_activated_disc_from_remain_disc_list(self):
        highest_activation = 0
        highest_idx = 0
        for idx, chunk in enumerate(self.disc_chunks):
            tmp_activation = actr.sdp(chunk.chunk_name, ':activation')[0][0]
            if tmp_activation > highest_activation:
                highest_activation = tmp_activation
                highest_idx = idx
        return self.disc_chunks.pop(highest_idx).chunk_name

    def place_response_marker(self, model, coords, finger):
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
    pattern_parser = pattern_util.Pattern_parser()
    stimulus_map = pattern_parser.extract_patterns_from_all_stim(stimulus_map)

    response_data = {}
    pause_data = {}
    for size, stim_data_list in stimulus_map.items():
        for stim_data in stim_data_list:
            for times in range(0, SINGLE_TRIAL_REPEAT_NUM):
                actr_model = LongFoveaChunkingModel(ref_num_param, stim_data)
                actr_model.run_experiment(False, type_of_stimulus)
                # collect disc num result
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

            # print(response_data[size])

        # normalize the response_num to proportion
        sum_response_num = sum(response_data[size])
        for idx in range(len(response_data[size])):
            response_data[size][idx] = response_data[size][idx] / sum_response_num
        print(response_data[size])

    file_io_util.save_simulation_data(response_data, ref_num_param)
    return response_data, pause_data


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
            # loss += (tmp_human_proportion - tmp_model_proportion) ** 2
            loss += abs(tmp_human_proportion - tmp_model_proportion)
    # return loss / n
    return loss


def get_best_fit_param(starting_param, iterations=100, stopping_threshold=1e-5, min_loss=1e-4,
                       type_of_stimulus=VERY_SHORT_STIMULUS_TYPE):
    human_data = file_io_util.load_human_data_from_csv()

    previous_loss = 2
    cur_param = starting_param
    for i in range(iterations):
        model_data = get_batch_result(cur_param, type_of_stimulus)
        cur_loss = get_loss_func_result(model_data, human_data)
        print(f"Iteration {i + 1}: Cost {cur_loss}, Reference_Count_Param {cur_param}")

        if previous_loss and (abs(previous_loss - cur_loss) < stopping_threshold or cur_loss < min_loss):
            return [cur_param, cur_loss]

        cur_param = cur_param + ((previous_loss - cur_loss) * FITTING_LEARNING_RATE)
        previous_loss = cur_loss

    return [cur_param, cur_loss]


def iterate_params_by_step(starting_param, step=1, iterations=20, type_of_stimulus=VERY_SHORT_STIMULUS_TYPE):
    human_data = file_io_util.load_human_data_from_csv()

    cur_param = starting_param
    for i in range(iterations):
        model_data, pause_data = get_batch_result(cur_param, type_of_stimulus)
        cur_loss = get_loss_func_result(model_data, human_data)
        print(f"Iteration {i + 1}: Cost {cur_loss}, Reference_Count_Param {cur_param}")
        cur_param += step

        file_io_util.save_pause_data(pause_data)

    return [cur_param, cur_loss]


# test functions
def test(type_of_stimulus, stim_size=9):
    stimulus_map = file_io_util.load_stimulus_from_csv()
    pattern_parser = pattern_util.Pattern_parser()
    stimulus_map = pattern_parser.extract_patterns_from_all_stim(stimulus_map)
    trial_stim_data = stimulus_map.get(stim_size)[10]

    test = LongFoveaChunkingModel(TOTAL_REFERENCE_NUM, trial_stim_data)
    test.run_experiment(True, type_of_stimulus)
    print(test.responded_disc_num)
    print(test.get_pause())


def test_regression_result():
    human_data = file_io_util.load_human_data_from_csv()
    model_data = file_io_util.load_simulation_data(12.904283761306571)
    loss = get_loss_func_result(model_data, human_data, stim_size_min=8, stim_size_max=9)
    print(loss)


def main():
    test(LONG_STIMULUS_TYPE,9)
    # test(SHORT_STIMULUS_TYPE)
    # human_data = file_io_util.load_human_data_from_csv()
    # model_data = file_io_util.load_simulation_data(TOTAL_REFERENCE_NUM)
    # loss = get_loss_func_result(model_data, human_data)
    # print('REFE_COUNT_PARAM = ' + str(TOTAL_REFERENCE_NUM) + ' ;loss = ' + str(loss))
    # get_batch_result(TOTAL_REFERENCE_NUM)

    # get_best_fit_param(TOTAL_REFERENCE_NUM)
    # test_regression_result()




if __name__ == '__main__':
    main()
