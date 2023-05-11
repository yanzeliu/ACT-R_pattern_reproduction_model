SQUARE_TAG = 'SQ'
TRIANGLE_TAG = 'TR'
CROSS_TAG = 'CR'
LINE_TAG = 'LI'
DISC_TAG = 'DI'
GROUP_TAG = 'GR'

# for salience override level: Square > triangle > Cross > Line
import numpy as np

class stimulus_data:

    def __init__(self, stim_x, stim_y):
        self.stim_x = stim_x
        self.stim_y = stim_y
        self.pattern_tag = [DISC_TAG] * len(stim_x)
        self.pattern_map = {}
        self.pattern_list = []
        self.pattern_tuple_for_disc = {}
        for idx in range(len(stim_x)):
            self.pattern_tuple_for_disc[idx] = []
        self.loc_on_visicon = np.zeros([len(stim_x), 2])

    def get_stim_locs(self):
        return self.stim_x, self.stim_y

    def set_pattern_tag(self, vertex_idx, pattern_type_tag):
        vertex_idx = np.sort(vertex_idx)

        for idx in vertex_idx:
            self.pattern_tag[idx] = pattern_type_tag
            self.pattern_tuple_for_disc[idx].append((pattern_type_tag, vertex_idx))

        if pattern_type_tag in self.pattern_map:
            self.pattern_map[pattern_type_tag].append(vertex_idx)
        else:
            self.pattern_map[pattern_type_tag] = [vertex_idx]

        self.pattern_list.append((pattern_type_tag, vertex_idx))
