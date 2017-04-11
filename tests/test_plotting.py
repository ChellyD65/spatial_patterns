__author__ = 'simonweber'
import unittest
import numpy as np
from learning_grids import plotting

class TestPlotting(unittest.TestCase):
	def setUp(self):
		self.plot = plotting.Plot()
	def test_get_spiketimes(self):
		firing_rates = np.array([0.4, 0.0, 8.0, 0.0, 0.0, 5.0])
		rate_factor = 20
		random_numbers = np.array([1.0, 0.8, 5.0, 0.3, 4.0, 3.0]) / rate_factor
		dt = 0.01
		expected = [0.02, 0.05]
		result = self.plot.get_spiketimes(firing_rates,
										  dt,
										  rate_factor,
										  random_numbers=random_numbers)
		np.testing.assert_array_equal(expected, result)
