# import pdb
import numpy as np
import utils
import output
# from scipy.stats import norm

def get_random_positions_within_circle(n, r, multiplicator=10):
	"""Returns n random 2 D positions within radius (rejection sampling)

	Parameters		
	----------
	n: number of positions
	r: radius
	multiplicator: to ensure that the rejection doesn't reduce the
					positions below n
	Returns
	-------
	ndarray of shape (n, 2)
	"""
	# random coords shape (n, 2)
	random_nrs = 2*r * np.random.random_sample((multiplicator * n, 2)) - r
	# difference squared
	ds = np.sum(np.power(random_nrs, 2), axis=1)
	# boolean arra
	b = ds < r**2
	# survivors: points within the circle
	survivors = random_nrs[b] 
	# slice the survivors to keep only n
	return survivors[:n]


class Synapses:
	"""
	The class of excitatory and inhibitory synapses

	Notes:
		- Given the synapse_type, it automatically gets the appropriate
			parameters from params
	"""
	def __init__(self, sim_params, type_params):
		# self.params = params
		for k, v in sim_params.items():
			setattr(self, k, v)

		for k, v in type_params.items():
			setattr(self, k, v)
		# self.type = synapse_type
		# self.n = params['n_' + self.type]
		# So far we take the sigma fixed
		# Maybe change to sigma array one day
		# self.sigma = params['sigma_' + self.type]
		self.sigmas = np.ones(self.n) * self.sigma
		self.twoSigma2 = 1. / (2 * self.sigma**2)
		self.norm = 1. / (self.sigma * np.sqrt(2 * np.pi))
		self.norm2 = 1. / (self.sigma**2 * 2 * np.pi)
		self.radius = self.boxlength / 2.
		# self.init_weight_noise = params['init_weight_noise_' + self.type]
		# Create weights array adding some noise to the init weights
		self.weights = (
			(1 + self.init_weight_noise *
			(2 * np.random.random_sample(self.n) - 1)) *
			self.init_weight
		)
		self.initial_weight_sum = np.sum(self.weights)
		self.initial_squared_weight_sum = np.sum(np.square(self.weights))
		self.eta_dt = self.eta * self.dt
		if self.dimensions == 1:
			# self.centers = np.linspace(0.0, 1.0, self.n)
			self.centers = (self.boxlength+2*self.weight_overlap)*np.random.random_sample(self.n)-self.weight_overlap
			# sort the centers
			self.centers.sort(axis=0)
		if self.dimensions == 2:
			if self.boxtype == 'linear':
				self.centers = (self.boxlength+2*self.weight_overlap)*np.random.random_sample((self.n, 2))-self.weight_overlap
			if self.boxtype == 'circular':
				self.centers = get_random_positions_within_circle(self.n, self.radius + self.weight_overlap)
	def set_rates(self, position):
		"""
		Computes the values of all place field Gaussians at <position>

		Future Tasks:
			- 	Maybe do not normalize because the normalization can be put into the
				weights anyway
			- 	Make it work for arbitrary dimensions
		"""
		if self.dimensions == 1:
			self.rates = self.norm*np.exp(-np.power(position - self.centers, 2)*self.twoSigma2)
		if self.dimensions == 2:
			self.rates =  (
				self.norm2
				* np.exp(-np.sum(np.power(position - self.centers, 2), axis=1) * self.twoSigma2)
			)

class Rat:
	"""
	The class of the rat
	"""
	def __init__(self, params):
		self.params = params
		for k, v in params['sim'].items():
			setattr(self, k, v)
		for k, v in params['out'].items():
			setattr(self, k, v)
		np.random.seed(int(self.params['sim']['seed_network']))
		self.x = self.initial_x
		self.y = self.initial_y
		self.phi = np.random.random_sample() * 2. * np.pi
		self.angular_sigma = np.sqrt(2. * self.velocity * self.dt / self.persistence_length)
		self.velocity_dt = self.velocity * self.dt
		self.dspace = np.sqrt(2.0*self.diff_const*self.dt)
		self.populations = ['exc', 'inh']
		self.radius = self.boxlength/2.
		self.radius_sq = self.radius**2
		self.synapses = {}
		for p in self.populations:
			self.synapses[p] = Synapses(params['sim'], params[p])

		self.steps = np.arange(1, self.simulation_time / self.dt + 1)

	def move_diffusively(self):
		"""
		Update position of rat by number drawn from gauss with stdev = dspace
		"""
		if self.dimensions == 1:
			self.x += self.dspace*np.random.randn()
		if self.dimensions == 2:
			self.x += self.dspace*np.random.randn()
			self.y += self.dspace*np.random.randn()

	def move_persistently(self):
		"""
		Move rat along direction phi and update phi according to persistence length
		"""
		if self.dimensions == 1:
			self.x += self.velocity_dt
		if self.dimensions == 2:
			# Boundary conditions and movement are interleaved here
			if self.x > self.boxlength or self.x < 0:
				is_x_bound_trespassed = True
			else:
				is_x_bound_trespassed = False

			if self.y > self.boxlength or self.y < 0:
				is_y_bound_trespassed = True
			else:
				is_y_bound_trespassed = False
			# Reflection at the corners
			if is_x_bound_trespassed and is_y_bound_trespassed:
				self.phi += np.pi
				self.x += self.velocity_dt * np.cos(self.phi)
				self.y += self.velocity_dt * np.sin(self.phi)
			# Reflection at left and right
			elif is_x_bound_trespassed:
				self.phi = np.pi - self.phi
				self.x += self.velocity_dt * np.cos(self.phi)
				self.y += self.velocity_dt * np.sin(self.phi)
			# Reflection at top and bottom
			elif is_y_bound_trespassed:
				self.phi = -self.phi
				self.x += self.velocity_dt * np.cos(self.phi)
				self.y += self.velocity_dt * np.sin(self.phi)
			# Normal move without reflection	
			else:
				self.phi += self.angular_sigma * np.random.randn()
				self.x += self.velocity_dt * np.cos(self.phi)
				self.y += self.velocity_dt * np.sin(self.phi)

	def move_persistently_circular(self):
		# Check if rat is outside and reflect it
		if self.x**2 + self.y**2 > self.radius_sq:
			theta = np.arctan(self.y/self.x)
			u_tangent = [-np.sin(theta), np.cos(theta)]
			u = [np.cos(self.phi), np.sin(self.phi)]
			alpha = np.arccos(np.dot(u_tangent, u))
			self.phi += 2 * alpha
		# Normal move without reflection
		else:
			self.phi += self.angular_sigma * np.random.randn()
			self.x += self.velocity_dt * np.cos(self.phi)
			self.y += self.velocity_dt * np.sin(self.phi)			


	def reflective_BCs(self):
		"""
		Reflective Boundary Conditions

		If the rat moves beyond the boundary, it gets reflected inside the boundary
		by the amount it was beyond the boundary
		"""
		if self.dimensions == 1:
			dimension_list = ['x']
		if self.dimensions == 2:
			dimension_list = ['x', 'y']
		for d in dimension_list:
			v = getattr(self, d)
			if v < 0:
				setattr(self, d, v - 2. * v)
			if v > self.boxlength:
				setattr(self, d, v - 2. * (v - self.boxlength))

	def periodic_BCs(self):
		"""
		Periodic Boundary Conditions
		"""
		if self.dimensions == 1:
			dimension_list = ['x']
		if self.dimensions == 2:
			dimension_list = ['x', 'y']
		for d in dimension_list:
			v = getattr(self, d)
			if v < 0:
				setattr(self, d, v + self.boxlength)
			if v > self.boxlength:
				setattr(self, d, v - self.boxlength)

	def billiard_BCs(self):
		"""
		Billiard Boundary Conditions

		Incidence Angle = Emergent Angle
		"""
		pass
		# # Right and Left wall
		# if self.x > self.boxlength or self.x < 0:
		# 	self.phi = np.pi - self.phi
		# # Top and Bottom wall
		# if self.y > self.boxlength or self.y < 0:
		# 	self.phi = 2. * np.pi - self.phi

	def set_current_output_rate(self):
		"""
		Sums exc_weights * exc_rates and substracts inh_weights * inh_rates
		"""
		rate = (
			np.dot(self.synapses['exc'].weights, self.synapses['exc'].rates) -
			np.dot(self.synapses['inh'].weights, self.synapses['inh'].rates)
		)
		self.output_rate = utils.rectify(rate)

	def set_current_input_rates(self):
		"""
		Set the rates of the input neurons by using their place fields
		"""
		if self.dimensions == 1:
			self.synapses['exc'].set_rates(self.x)
			self.synapses['inh'].set_rates(self.x)
		if self.dimensions == 2:
			self.synapses['exc'].set_rates([self.x, self.y])
			self.synapses['inh'].set_rates([self.x, self.y])	

	def update_exc_weights(self):
		"""
		Update exc weights according to Hebbian learning
		"""
		self.synapses['exc'].weights += (
			self.synapses['exc'].rates * self.output_rate * self.synapses['exc'].eta_dt
		)

	def update_inh_weights(self):
		"""
		Update inh weights according to Hebbian learning with target rate
		"""
		self.synapses['inh'].weights += (
			self.synapses['inh'].rates *
				(self.output_rate - self.target_rate) * self.synapses['inh'].eta_dt
		)

	def update_weights(self):
		"""
		Update both weights (convenience function)
		"""
		self.update_exc_weights()
		self.update_inh_weights()

	def normalize_exc_weights_linear_substractive(self):
		"""Normalize substractively, keeping the linear sum constant"""
		# Get a vector with entries of ones and zeroes
		# For each synapse with positive values you get a one
		# For each synapase with negative values you get a zero
		# See Dayan, Abbott p. 290 for schema
		substraction_value = (
			self.synapses['exc'].eta_dt * self.output_rate
			* np.sum(self.synapses['exc'].rates) / self.synapses['exc'].n)
		n_vector = (self.synapses['exc'].weights > substraction_value).astype(int)

		substractive_norm = (
			self.synapses['exc'].eta_dt * self.output_rate
			* np.dot(self.synapses['exc'].rates, n_vector) * n_vector
			/ np.sum(n_vector)
		)
		self.synapses['exc'].weights -= substractive_norm

	def normalize_exc_weights_linear_multiplicative(self):
		"""Normalize multiplicatively, keeping the linear sum constant"""
		self.synapses['exc'].weights = (
			(self.synapses['exc'].initial_weight_sum / np.sum(self.synapses['exc'].weights)) *
			self.synapses['exc'].weights
		)

	def normalize_exc_weights_quadratic_multiplicative(self):
		"""Normalize  multiplicatively, keeping the quadratic sum constant"""
		self.synapses['exc'].weights = (
			np.sqrt((self.synapses['exc'].initial_squared_weight_sum /
											np.sum(np.square(self.synapses['exc'].weights)))) *
				self.synapses['exc'].weights
		)

	def run(self, rawdata_table=False, configuration_table=False):
		"""
		Let the rat move and learn

		Arguments:
		- 	position_output: if True, self.positions gets all the rat positions
			appended
		"""
		
		np.random.seed(int(self.params['sim']['seed_trajectory']))
		print 'Type of Normalization: ' + self.normalization
		print 'Type of Motion: ' + self.motion
		print 'Boundary Conditions: ' + self.boundary_conditions
		##########################################################
		##########	Choose Motion and Boundary Conds 	##########
		##########################################################
		if self.motion == 'diffusive':
			self.move = self.move_diffusively
		if self.motion == 'persistent' and self.boxtype == 'linear':
			self.move = self.move_persistently
		if self.motion == 'persistent' and self.boxtype == 'circular':
			self.move = self.move_persistently_circular
		# if self.boundary_conditions == 'reflective':
		# 	self.apply_boundary_conditions = self.reflective_BCs
		# if self.boundary_conditions == 'periodic':
		# 	self.apply_boundary_conditions = self.periodic_BCs
		self.apply_boundary_conditions = getattr(self, self.boundary_conditions + '_BCs')

		# Choose the normalization scheme
		normalize_exc_weights = getattr(self, 'normalize_exc_weights_' + self.normalization)

		rawdata = {'exc': {}, 'inh': {}}

		for p in ['exc', 'inh']:
			rawdata[p]['centers'] = self.synapses[p].centers
			rawdata[p]['sigmas'] = self.synapses[p].sigmas
			rawdata[p]['weights'] = np.empty((np.ceil(
								1 + self.simulation_time / self.every_nth_step_weights), self.synapses[p].n))
			rawdata[p]['weights'][0] = self.synapses[p].weights.copy()

		rawdata['positions'] = np.empty((np.ceil(
								1 + self.simulation_time / self.every_nth_step), 2))
		# rawdata['phi'] = np.empty(np.ceil(
		# 						1 + self.simulation_time / self.every_nth_step))
		rawdata['output_rates'] = np.empty(np.ceil(
								1 + self.simulation_time / self.every_nth_step))		
		
		# rawdata['phi'][0] = self.phi
		rawdata['positions'][0] = np.array([self.x, self.y])
		rawdata['output_rates'][0] = 0.0

		rawdata['time_steps'] = self.steps
		for step in self.steps:
			self.move()
			self.apply_boundary_conditions()
			self.set_current_input_rates()
			self.set_current_output_rate()
			self.update_weights()
			utils.rectify_array(self.synapses['exc'].weights)
			utils.rectify_array(self.synapses['inh'].weights)
			normalize_exc_weights()
			
			if step % self.every_nth_step == 0:
				index = step / self.every_nth_step
				# print 'step = %f' % step
				# Store Positions
				# print 'step %f position %f outputrate %f' % (step, self.x, self.output_rate)
				rawdata['positions'][index] = np.array([self.x, self.y])
				# rawdata['phi'][index] = np.array(self.phi)
				rawdata['output_rates'][index] = self.output_rate
				# print 'current step: %i' % step

			if step % self.every_nth_step_weights == 0:
				print 'Current step: %i' % step
				index = step / self.every_nth_step_weights
				rawdata['exc']['weights'][index] = self.synapses['exc'].weights.copy()
				rawdata['inh']['weights'][index] = self.synapses['inh'].weights.copy()
		# Convert the output into arrays
		# for k in rawdata:
		# 	rawdata[k] = np.array(rawdata[k])
		# rawdata['output_rates'] = np.array(rawdata['output_rates'])
		print 'Simulation finished'
		return rawdata

