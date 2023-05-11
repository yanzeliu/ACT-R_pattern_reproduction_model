import os

import numpy as np
from scipy.spatial import Delaunay
import scipy
import itertools
import stimulus_util
import cv2
import matplotlib.pyplot as plt
import pickle

EDGE_LENGHT_IDENTICAL_THRESHOLD = 17
ANGLE_THRESHOLD_IN_RADIUS = np.pi / 36

DISTORTED_LENGTH_THRESHOLD = 0.15

MAX_INGROUP_DISC_NUM = 4

# ANGLE_THRESHOLD_IN_RADIUS = np.pi / 60

class Pattern_parser:

    def __init__(self):
        self.disc_chunks = None

    def get_square_patterns(self, disc_chunks, attending_location):
        for disc in disc_chunks:
            print(disc.x)

    def extract_patterns_from_all_stim(self, stimulus_map):
        saved_stimulus_map = self.load_saved_result_if_pickle_exist()
        if saved_stimulus_map is not None:
            return saved_stimulus_map

        for size, stim_data_list in stimulus_map.items():
            if size < 3:
                continue
            for stim_data in stim_data_list:
                tri_result = self.get_delaunay_triangulation(stim_data)

                ## code for test
                # plot_triangulation_result(tri_result)

                self.labelling_equilateral_triangle(stim_data, tri_result)
                self.labelling_square(stim_data, tri_result)
                self.labelling_distorted_square(stim_data, tri_result)
                self.split_non_pattern_disc_into_groups(stim_data, tri_result)
        return stimulus_map

    def load_saved_result_if_pickle_exist(self):
        if os.path.exists('stimulus_map.pickle'):
            with open('stimulus_map.pickle', 'rb') as handle:
                stimulus_map = pickle.load(handle)
            return stimulus_map
        else:
            return None

    def get_delaunay_triangulation(self, stim_data):
        coord_arr = []
        for x, y in zip(stim_data.stim_x, stim_data.stim_y):
            coord_arr.append([x, y])
        points = np.array(coord_arr)
        tri = Delaunay(points)
        return tri

    def labelling_equilateral_triangle(self, stim_data, tri_result):
        points = tri_result.points
        simplices = tri_result.simplices
        for simplex_vertex_idx in simplices:
            vertexes = points[simplex_vertex_idx]
            pre_edge_len = -1
            is_equilateral = True
            for comb in itertools.combinations(vertexes, 2):
                cur_edge_len = np.linalg.norm(comb[1] - comb[0])
                if pre_edge_len == -1 or abs(pre_edge_len - cur_edge_len) <= EDGE_LENGHT_IDENTICAL_THRESHOLD:
                    pre_edge_len = cur_edge_len
                else:
                    is_equilateral = False
                    break
            # print(is_equilateral)
            if is_equilateral:
                # print(stimulus_util.TRIANGLE_TAG)
                stim_data.set_pattern_tag(simplex_vertex_idx, stimulus_util.TRIANGLE_TAG)
            # np.linalg.norm(vertex[0] - vertex[1])

    def labelling_cross(self, stim_data, tri_result):
        points = tri_result.points
        simplices = tri_result.simplices
        # find a isosceles right triangle
        for simplex_vertex_idx in simplices:
            vertexes = points[simplex_vertex_idx]
            is_isosceles_tag, bevel_edge_vertexes_idx = self.check_if_a_isosceles_right_triangle(vertexes,
                                                                                                 simplex_vertex_idx)[:2]
            if is_isosceles_tag:
                # check simplices which contain the right angle vertex are all isosceles right
                for simplex in simplices:
                    contain_bevel_edge = np.all(np.isin(bevel_edge_vertexes_idx, simplex))

    def labelling_square(self, stim_data, tri_result):
        points = tri_result.points
        simplices = tri_result.simplices
        for simplex_vertex_idx in simplices:
            vertexes = points[simplex_vertex_idx]
            is_isosceles_tag, bevel_edge_vertexes_idx = self.check_if_a_isosceles_right_triangle(vertexes,
                                                                                                 simplex_vertex_idx)[:2]
            if is_isosceles_tag:
                ## find neighbor which shared the same bevel edge
                for simplex in simplices:
                    contain_bevel_edge = np.all(np.isin(bevel_edge_vertexes_idx, simplex))
                    third_vertex = simplex_vertex_idx[~ np.isin(simplex_vertex_idx, bevel_edge_vertexes_idx)]
                    not_contain_third_vertex = ~ (np.isin(third_vertex, simplex)[0])
                    if contain_bevel_edge and not_contain_third_vertex:
                        is_isosceles, bevel_edge_idx, top_vertex_idx = self.check_if_a_isosceles_right_triangle(
                            points[simplex], simplex)
                        ## check the shared edge are both bevel edge
                        not_right_angle_edge = ~ np.isin(top_vertex_idx, bevel_edge_vertexes_idx)
                        if is_isosceles and not_right_angle_edge:
                            square_idx = np.unique(np.concatenate((simplex, simplex_vertex_idx), axis=None))
                            stim_data.set_pattern_tag(square_idx, stimulus_util.SQUARE_TAG)
                            # test code
                            # self.plot_triangulation_result(tri_result)
                            # print(points[square_idx])


    def labelling_distorted_square(self, stim_data, tri_result):
        points = tri_result.points
        simplices = tri_result.simplices
        for simplex_vertex_idx in simplices:
            vertexes = points[simplex_vertex_idx]
            is_isosceles_tag, bevel_edge_vertexes_idx = self.check_if_a_isosceles_right_triangle(vertexes, simplex_vertex_idx)[:2]
            if is_isosceles_tag:
                # get the location of the fourth vertex of the square
                # find the right angle vertex
                right_angle_vertex_idx = simplex_vertex_idx[~ np.isin(simplex_vertex_idx, bevel_edge_vertexes_idx)]
                # get the vector of the right-angle sides
                right_angle_vector_1 = points[bevel_edge_vertexes_idx[0]] - points[right_angle_vertex_idx]
                right_angle_vector_2 = points[bevel_edge_vertexes_idx[1]] - points[right_angle_vertex_idx]
                right_angle_vector_1 = np.append(right_angle_vector_1, 0)
                right_angle_vector_2 = np.append(right_angle_vector_2, 0)
                # get the cross product of the two right-angle vectors
                cross_product = np.cross(right_angle_vector_1, right_angle_vector_2)
                square_edge_vector_3 = np.cross(right_angle_vector_1, cross_product)
                square_edge_vector_4 = np.cross(right_angle_vector_2, cross_product)
                vector_3_end_point = square_edge_vector_3[:2] + points[bevel_edge_vertexes_idx[0]]
                vector_4_end_point = square_edge_vector_4[:2] + points[bevel_edge_vertexes_idx[1]]
                # get the intersection of the two square edge vectors
                square_vertex_4 = self.line_intersection((points[bevel_edge_vertexes_idx[0]], vector_3_end_point),
                                                         (points[bevel_edge_vertexes_idx[1]], vector_4_end_point))
                distance_threshold = DISTORTED_LENGTH_THRESHOLD * np.linalg.norm(right_angle_vector_1)
                for idx, point in enumerate(points):
                    # calculate the distance between the point and the square vertex
                    distance = np.linalg.norm(point - square_vertex_4)
                    if distance < distance_threshold:
                        square_idx =  np.concatenate((simplex_vertex_idx, [idx]), axis=None)
                        stim_data.set_pattern_tag(square_idx, stimulus_util.SQUARE_TAG)

                        # test code
                        # if len(points) == 9:
                        #     self.plot_triangulation_result(tri_result)
                        #     print(point)


    def labelling_line(self, stim_data, tri_result):
        points = tri_result.points
        point = cv2.Mat(np.float32(points), wrap_channels=2)

        rhoMin = 0.0
        rhoMax = 360.0
        rhoStep = 1
        thetaMin = 0.0
        thetaStep = np.pi / 180.0
        thetaMax = np.pi - thetaStep
        lines_max = 3
        threshold = 2
        lines = cv2.HoughLinesPointSet(point, lines_max, threshold, rhoMin, rhoMax, rhoStep, thetaMin, thetaMax,
                                       thetaStep)

        if lines is not None:
            print(lines)
            self.plot_triangulation_result(tri_result)


    def check_if_a_isosceles_right_triangle(self, vertexes, vertex_idx):
        bevel_edge_vertexes_idx = []
        isosceles_tag = False
        top_vertex = None
        ## calcuate one angle
        angle_1 = self.calcuate_angle_between_vectors(vertexes[1] - vertexes[0], vertexes[2] - vertexes[0])
        ## if angle_1 is 90 degrees
        if abs(angle_1 - (np.pi / 2)) < ANGLE_THRESHOLD_IN_RADIUS:
            angle_2 = self.calcuate_angle_between_vectors(vertexes[0] - vertexes[1], vertexes[2] - vertexes[1])

            ## and angle_2 is 45 degrees, then 1_2 is the bevel edge
            if abs(angle_2 - (np.pi / 4)) < ANGLE_THRESHOLD_IN_RADIUS:
                bevel_edge_vertexes_idx = [vertex_idx[1], vertex_idx[2]]
                isosceles_tag = True
                top_vertex = vertex_idx[0]

        ## if angle_1 is 45 degrees
        elif abs(angle_1 - (np.pi / 4)) < ANGLE_THRESHOLD_IN_RADIUS:
            angle_2 = self.calcuate_angle_between_vectors(vertexes[0] - vertexes[1], vertexes[2] - vertexes[1])

            ## and angle_2 is 90 degrees, then 0_2 is the bevel edge
            if abs(angle_2 - (np.pi / 2)) < ANGLE_THRESHOLD_IN_RADIUS:
                bevel_edge_vertexes_idx = [vertex_idx[0], vertex_idx[2]]
                isosceles_tag = True
                top_vertex = vertex_idx[1]

            ## and angle_2 is 45 degrees too, then 0_1 is the bevel edge
            elif abs(angle_2 - (np.pi / 4)) < ANGLE_THRESHOLD_IN_RADIUS:
                bevel_edge_vertexes_idx = [vertex_idx[0], vertex_idx[1]]
                isosceles_tag = True
                top_vertex = vertex_idx[2]
        return isosceles_tag, bevel_edge_vertexes_idx, top_vertex

    def calcuate_angle_between_vectors(self, vector_1, vector_2):
        unit_vector_1 = vector_1 / np.linalg.norm(vector_1)
        unit_vector_2 = vector_2 / np.linalg.norm(vector_2)
        dot_product = np.dot(unit_vector_1, unit_vector_2)
        angle = np.arccos(dot_product)
        # print(angle)
        return angle

    # line1 tuples (x1, y1)
    # line2 tuples (x2, y2)
    def line_intersection(self, line1, line2):
        xdiff = (line1[0][0] - line1[1][0], line2[0][0] - line2[1][0])
        ydiff = (line1[0][1] - line1[1][1], line2[0][1] - line2[1][1])

        def det(a, b):
            return a[0] * b[1] - a[1] * b[0]

        div = det(xdiff, ydiff)
        if div == 0:
            raise Exception('lines do not intersect')

        d = (det(*line1), det(*line2))
        x = det(d, xdiff) / div
        y = det(d, ydiff) / div
        return x, y

    def split_non_pattern_disc_into_groups(self, stim_data, tri_result):
        points = tri_result.points
        non_pattern_disc_idx = np.where(np.array(stim_data.pattern_tag) == stimulus_util.DISC_TAG)
        non_pattern_points = points[non_pattern_disc_idx]
        if len(non_pattern_points) == 0:
            return

        # get max edge length of all the patterns
        max_edge_length = 0
        pattern_disc_idx = np.where(np.array(stim_data.pattern_tag) != stimulus_util.DISC_TAG)
        pattern_points = points[pattern_disc_idx]
        for i in range(len(pattern_points)):
            for j in range(i + 1, len(pattern_points)):
                tmp_distance = np.linalg.norm(pattern_points[i] - pattern_points[j])
                if tmp_distance > max_edge_length:
                    max_edge_length = tmp_distance

        # create a sparse matrix to store the distance between each pair of points
        distance_matrix = scipy.sparse.lil_matrix((len(non_pattern_points), len(non_pattern_points)))
        # calculate the distance between each pair of points
        for i in range(len(non_pattern_points)):
            for j in range(i + 1, len(non_pattern_points)):
                distance_matrix[i, j] = np.linalg.norm(non_pattern_points[i] - non_pattern_points[j])
                distance_matrix[j, i] = distance_matrix[i, j]
        # get the minimum spanning tree
        mst = scipy.sparse.csgraph.minimum_spanning_tree(distance_matrix)

        # remove the edges which are longer than the threshold
        if max_edge_length > 0:
            mst.data[mst.data > max_edge_length] = 0
            mst.eliminate_zeros()

        # get the connected components
        n_components, labels = scipy.sparse.csgraph.connected_components(mst, directed=False)
        # get the size of each connected component
        unique, counts = np.unique(labels, return_counts=True)
        max_component_size = np.max(counts)
        while max_component_size > MAX_INGROUP_DISC_NUM:
            mst.data[np.argmax(mst.data)] = 0
            mst.eliminate_zeros()
            n_components, labels = scipy.sparse.csgraph.connected_components(mst, directed=False)
            unique, counts = np.unique(labels, return_counts=True)
            max_component_size = np.max(counts)

        for label_tag in unique:
            label_idx = np.where(labels == label_tag)
            stim_data.set_pattern_tag(np.array(non_pattern_disc_idx[0])[label_idx], stimulus_util.GROUP_TAG)

        # self.plot_stimulus(stim_data)


    def plot_triangulation_result(self, tri_result):
        points = tri_result.points
        plt.triplot(points[:, 0], points[:, 1], tri_result.simplices)
        plt.plot(points[:, 0], points[:, 1], 'o')
        plt.show()

    def plot_stimulus(self, stim_data):
        stim_x = np.array(stim_data.stim_x).astype(np.float64)
        stim_y = np.array(stim_data.stim_y).astype(np.float64)
        for pattern in stim_data.pattern_list:
            print(pattern)
            tar_point_idx = pattern[1]
            plt.plot(stim_x[tar_point_idx], stim_y[tar_point_idx], 'o')
        plt.show()

# # test code
def main():
    import file_io_util
    stimulus_map = file_io_util.load_stimulus_from_csv()
    pattern_parser = Pattern_parser()
    stimulus_map = pattern_parser.extract_patterns_from_all_stim(stimulus_map)
    with open('stimulus_map.pickle', 'wb') as handle:
        pickle.dump(stimulus_map, handle, protocol=pickle.HIGHEST_PROTOCOL)
    with open('stimulus_map.pickle', 'rb') as handle:
        b = pickle.load(handle)
    print(b)

def test_serialization():
    import file_io_util

    import scipy.spatial
    with open('stimulus_map.pickle', 'rb') as handle:
        stimulus_map = pickle.load(handle)
    # find a stimulus which has a pattern
    test_num = 10
    for stim in stimulus_map[9]:
        # if bool(stim.pattern_map):
        if np.size(np.where(np.array(stim.pattern_tag) == stimulus_util.GROUP_TAG)) < 9:
            stim_x = np.array(stim.stim_x).astype(np.float64)
            stim_y = np.array(stim.stim_y).astype(np.float64)
            for pattern in stim.pattern_list:
                print(pattern)
                tar_point_idx = pattern[1]
                plt.plot(stim_x[tar_point_idx],stim_y[tar_point_idx], 'o')
            plt.show()
            print('*' * 20)
            test_num -= 1
            if test_num == 0:
                break
            # tri = scipy.spatial.Delaunay(np.array([stim_x, stim_y]).T)
            # for pattern_key in iter(stim.pattern_map):
            #     for pattern_idx_arr in stim.pattern_map[pattern_key]:
            #         # plt.plot(stim_x[pattern_idx_arr],stim_y[pattern_idx_arr])
            #         # plot dots not in pattern_idx_arr
            #         pattern_idx_arr = np.array(pattern_idx_arr)
            #         not_in_pattern_idx_arr = np.setdiff1d(np.arange(len(stim_x)), pattern_idx_arr)



if __name__ == '__main__':
    main()
    # test_serialization()

