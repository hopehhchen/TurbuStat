
'''
Test functions for SCF
'''

import numpy as np

from ..statistics import SCF, SCF_Distance
from ._testing_data import dataset1, dataset2, computed_data, computed_distances

class testSCF():

    def __init__(self):
        self.dataset1 = dataset1
        self.dataset2 = dataset2
        self.computed_data = computed_data
        self.computed_distances = computed_distances
        self.tester = None

    def test_SCF_method(self):
        self.tester = SCF(dataset1["cube"][0], size = 11)
        self.tester.run()
        assert np.allclose(self.tester.scf_surface, self.computed_data['scf_val'])

    def test_SCF_distance(self):
        self.tester_dist = SCF_Distance(dataset1["cube"][0],dataset2["cube"][0], fiducial_model = self.tester).distance_metric().distance
        assert np.allclose(self.tester_dist, self.computed_distances['scf_distance'])