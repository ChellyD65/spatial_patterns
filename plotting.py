import matplotlib as mpl
import math
# mpl.use('TkAgg')
import matplotlib.pyplot as plt
import numpy as np
import scipy.stats
import initialization
import general_utils.arrays
import utils
mpl.rcParams.update({'figure.autolayout': True})
# print mpl.rcParams.keys()
# mpl.rcParams['animation.frame_format'] = 'jpeg'
# print mpl.rcParams['animation.frame_format']

def plot_list(fig, plot_list):
	"""
	Takes a list of lambda forms of plot functions and plots them such that
	no more than four rows are used to assure readability
	"""
	n_plots = len(plot_list)
	for n, p in enumerate(plot_list, start=1):
		if n_plots < 4:
			fig.add_subplot(n_plots, 1, n)
		else:
			fig.add_subplot(math.ceil(n_plots/2.), 2, n)
		p()

def set_current_output_rate(self):
	"""
	Sums exc_weights * exc_rates and substracts inh_weights * inh_rates
	"""
	rate = (
		np.dot(self.exc_syns.weights, self.exc_syns.rates) -
		np.dot(self.inh_syns.weights, self.inh_syns.rates)
	)
	self.output_rate = utils.rectify(rate)

def set_current_input_rates(self):
	"""
	Set the rates of the input neurons by using their place fields
	"""
	self.exc_syns.set_rates(self.x)
	self.inh_syns.set_rates(self.x)

class Plot(initialization.Synapses):
	"""The Plotting Class"""
	def __init__(self, params, rawdata):
		self.params = params
		self.rawdata = rawdata
		for k, v in params['sim'].items():
			setattr(self, k, v)
		for k, v in params['out'].items():
			setattr(self, k, v)
		for k, v in rawdata.items():
			setattr(self, k, v)

		self.box_linspace = np.linspace(-self.radius, self.radius, 200)
		self.time = np.arange(0, self.simulation_time + self.dt, self.dt)
		self.colors = {'exc': 'g', 'inh': 'r'}
		# self.fig = plt.figure()

	def spike_map(self, small_dt, start_frame=0, end_frame=-1):
		plt.xlim(-self.radius, self.radius)
		plt.ylim(-self.radius, self.radius)

		plt.plot(
			self.positions[start_frame:end_frame,0],
			self.positions[start_frame:end_frame,1], color='black', linewidth=0.5)

		rates_x_y = np.nditer(
			[self.output_rates[start_frame:end_frame],
			self.positions[start_frame:end_frame, 0],
			self.positions[start_frame:end_frame, 1]])
		for r, x, y in rates_x_y:
				if r * small_dt > np.random.random():
					plt.plot(x, y, marker='o',
						linestyle='none', markeredgecolor='none', markersize=3, color='r')
		title = '%.1e to %.1e' % (start_frame, end_frame)
		plt.title(title, fontsize=8)

		ax = plt.gca()		
		ax.set_aspect('equal')
		ax.set_xticks([])
		ax.set_yticks([])

	def output_rates_vs_position(self, start_frame=0, clipping=False):
		if self.dimensions == 1:
			_positions = self.positions[:,0][start_frame:,]
			_output_rates = self.output_rates[start_frame:,]
			plt.plot(_positions, _output_rates, linestyle='none', marker='o')
		if self.dimensions == 2:
			positions = self.positions[start_frame:,]
			output_rates = self.output_rates[start_frame:,]
			plt.xlim(-self.radius, self.radius)
			plt.ylim(-self.radius, self.radius)
			if clipping:
				color_norm = mpl.colors.Normalize(0, np.amax(output_rates)/10000.0)			
			else:
				color_norm = mpl.colors.Normalize(np.amin(output_rates), np.amax(output_rates))
			for p, r in zip(positions, output_rates):
				color = mpl.cm.YlOrRd(color_norm(r))
				plt.plot(p[0], p[1], linestyle='none', marker='s', markeredgecolor='none', color=color, markersize=5, alpha=0.5)
		ax = plt.gca()
		ax.set_aspect('equal')
		ax.set_xticks([])
		ax.set_yticks([])

	def get_rates(self, position, syn_type):
		"""
		Computes the values of all place field Gaussians at <position>

		Inherited from Synapses
		"""
		return self.set_rates(position, data=self.rawdata[syn_type])


	def get_output_rate(self, position, frame):
		"""
		Note: if you want it for several times don't calculate set_rates every time, because it does not change!!!
		"""
		return (
			np.dot(self.rawdata['exc']['weights'][frame], self.get_rates(position[0], 'exc')) 
			- np.dot(self.rawdata['inh']['weights'][frame], self.get_rates(position[0], 'inh')) 
		)

	def get_X_Y_positions_grid_rates_grid_tuple(self, spacing):
		"""
		Returns X, Y meshgrid and position_grid and rates_grid for contour plot

		RETURNS:
		- X, Y: meshgrids for contour plotting
		- positions_grid: array with all the positions in a matrix like shape:
			[ 
				[ 
					[x1, y1], [x1, y2]
				] , 
				[ 	
					[x2, y1], [x2, y2]
				]
			]
		- rates_grid: dictionary of two arrays, one exc and one inh.
				Following the matrix structure of positions_grid, each entry in this
				"matrix" (note: it is an array, not a np.matrix) is the array of
				firing rates of the neuron type at this position
		ISSUES:
		- Probably X, Y creation can be circumvented elegantly with the positions_grid
		- Since it is only used once per animation (it was created just for this purpose)
			it is low priority
		"""
		rates_grid = {}
		positions_grid = np.empty((spacing, spacing, 2))
		# Set up X, Y for contour plot
		x_space = np.linspace(-self.radius, self.radius, spacing)
		y_space = np.linspace(-self.radius, self.radius, spacing)
		X, Y = np.meshgrid(x_space, y_space)
		for n_y, y in enumerate(y_space):
			for n_x, x in enumerate(x_space):
				positions_grid[n_x][n_y] =  [x, y]

		positions_grid.shape = (spacing, spacing, 1, 1, 2)
		rates_grid['exc'] = self.get_rates(positions_grid, 'exc')
		rates_grid['inh'] = self.get_rates(positions_grid, 'inh')
		return X, Y, positions_grid, rates_grid

	def get_output_rates_from_equation(self, frame, spacing, positions_grid=False, rates_grid=False):
		"""
		Return output_rates at many positions for contour plotting

		ARGUMENTS:
		- frame: the frame number to be plotted
		- spacing: the spacing, describing the detail richness of the plor or contour plot (spacing**2)
		- positions_grid, rates_grid: Arrays as described in get_X_Y_positions_grid_rates_grid_tuple
		"""
		plt.title('output_rates, t = %.1e' % (frame * self.every_nth_step_weights), fontsize=8)

		if self.dimensions == 1:
			linspace = np.linspace(-self.radius, self.radius, spacing)
			output_rates = np.empty(spacing)
			for n, x in enumerate(linspace):
				output_rates[n] = self.get_output_rate([x, None], frame)
			output_rates = utils.rectify_array(output_rates)
			return linspace, output_rates

		if self.dimensions == 2:
			output_rates = np.empty((spacing, spacing))
			# Note how the tensor dot product is used
			output_rates = (
				np.tensordot(self.rawdata['exc']['weights'][frame], rates_grid['exc'], axes=([0], [2]))
				- np.tensordot(self.rawdata['inh']['weights'][frame], rates_grid['inh'], axes=([0], [2]))
			)
			# Transposing is necessary for the contour plot
			output_rates = np.transpose(output_rates)
			output_rates = utils.rectify_array(output_rates)
			return output_rates		


	def plot_output_rates_from_equation(self, frame=-1, spacing=101, fill=True):
		if self.dimensions == 1:
			linspace, output_rates = self.get_output_rates_from_equation(frame, spacing)
			plt.xlim(-self.radius, self.radius)
			plt.plot(linspace, output_rates, color='b')
		if self.dimensions == 2:
			# X, Y, output_rates = self.get_output_rates_from_equation(frame, spacing)
			X, Y, positions_grid, rates_grid = self.get_X_Y_positions_grid_rates_grid_tuple(spacing)
			output_rates = self.get_output_rates_from_equation(frame, spacing, positions_grid, rates_grid)
			# Hack to avoid error in case of vanishing output rate at every position
			# If every entry in output_rates is 0, you define a norm and set
			# one of the elements to a small value (such that it looks like zero)			
			if fill:
				if np.count_nonzero(output_rates) == 0:
					color_norm = mpl.colors.Normalize(0., 100.)
					output_rates[0][0] = 0.000001
					plt.contourf(X, Y, output_rates, norm=color_norm)
				else:
					plt.contourf(X, Y, output_rates)	
			else:
				if np.count_nonzero(output_rates) == 0:
					color_norm = mpl.colors.Normalize(0., 100.)
					output_rates[0][0] = 0.000001
					plt.contour(X, Y, output_rates, norm=color_norm)
				else:
					plt.contour(X, Y, output_rates)
			ax = plt.gca()
			ax.set_aspect('equal')
			ax.set_xticks([])
			ax.set_yticks([])


	def fields_times_weights(self, time=-1, syn_type='exc', normalize_sum=True):
		"""
		Plots the Gaussian Fields multiplied with the corresponding weights

		Arguments:
		- time: default -1 takes weights at the last moment in time
				Warning: if time_step != 1.0 this doesn't work, because
				you take the array at index [time]
		- normalize_sum: If true the sum gets scaled such that it
			is comparable to the height of the weights*gaussians,
			this way it is possible to see the sum and the individual
			weights on the same plot. Otherwise the sum would be way larger.
		"""
		plt.title(syn_type + ' fields x weights', fontsize=8)
		x = self.box_linspace
		t = syn_type
		# colors = {'exc': 'g', 'inh': 'r'}	
		summe = 0
		divisor = 1.0
		if normalize_sum:
			# divisor = 0.5 * len(rawdata[t + '_centers'])
			divisor = 0.5 * self.params[syn_type]['n']			
		for c, s, w in np.nditer([
						self.rawdata[t]['centers'],
						self.rawdata[t]['sigmas'],
						self.rawdata[t]['weights'][time] ]):
			gaussian = scipy.stats.norm(loc=c, scale=s).pdf
			l = plt.plot(x, w * gaussian(x), color=self.colors[syn_type])
			summe += w * gaussian(x)
		plt.plot(x, summe / divisor, color=self.colors[syn_type], linewidth=4)
		# return l

	def fields(self, show_sum=False):
		"""
		Plotting of Gaussian Fields and their sum

		Note: The sum gets divided by a something that depends on the 
				number of cells of the specific type, to make it fit into
				the frame (see note in fields_times_weighs)
		"""
		x = self.box_linspace
		# Loop over different synapse types and color tuples
		plt.xlim([-self.radius, self.radius])
		for t, color in [('exc', 'g'), ('inh', 'r')]:
			summe = 0
			for c, s in np.nditer([self.rawdata[t]['centers'], self.rawdata[t]['sigmas']]):
				gaussian = scipy.stats.norm(loc=c, scale=s).pdf
				plt.plot(x, gaussian(x), color=color)
				summe += gaussian(x)
			if show_sum:
				plt.plot(x, 2*summe/(len(getattr(self, t + '_centers'))), color=color, linewidth=4)
		return

	def weights_vs_centers(self, syn_type='exc', frame=-1):
		"""Plots the current weight at each center"""
			
		plt.title(syn_type + ' Weights vs Centers' + ', ' + 'Frame = ' + str(frame), fontsize=8)	
		plt.xlim(-self.radius, self.radius)
		centers = self.rawdata[syn_type]['centers']
		weights = self.rawdata[syn_type]['weights'][frame]
		plt.plot(centers, weights, color=self.colors[syn_type], marker='o')

	def weight_evolution(self, syn_type='exc', time_sparsification=1, weight_sparsification=1):
		"""
		Plots the time evolution of synaptic weights.

		----------
		Arguments:
		- syn_type: type of the synapse
		- time_sparsification: factor by which the time resolution is reduced
		- weight_sparsification: factor by which the number of weights is reduced

		----------
		Remarks:
		- If you use an already sparsified weight array as input, the center color-coding
			won't work
		"""
		plt.title(syn_type + ' weight evolution', fontsize=8)
		# Create time array, note that you need to add 1, because you also have time 0.0
		time = np.linspace(
			0, self.simulation_time,
			num=self.simulation_time / time_sparsification / self.every_nth_step_weights + 1)
		# Loop over individual weights (using sparsification)
		# Notet the the arange takes as an (excluded) endpoint the length of the first weight array
		# assuming that the number of weights is constant during the simulation
		for i in np.arange(0, len(self.rawdata[syn_type]['weights'][0]), weight_sparsification):
			# Create array of the i-th weight for all times
			weight = self.rawdata[syn_type]['weights'][:,i]
			center = self.rawdata[syn_type]['centers'][i]
			# Take only the entries corresponding to the sparsified times
			weight = general_utils.arrays.take_every_nth(weight, time_sparsification)	
			if self.dimensions == 2:
				center = center[0]

			# if self.params['exc']['fields_per_synapse'] == 1 and self.params['inh']['fields_per_synapse'] == 1:
			# 	# Specify the range of the colormap
			# 	color_norm = mpl.colors.Normalize(-self.radius, self.radius)
			# 	# Set the color from a color map
			# 	print center
			# 	color = mpl.cm.rainbow(color_norm(center))
			# 	plt.plot(time, weight, color=color)
			# else:
			plt.plot(time, weight)

	def output_rate_distribution(self, start_time=0):
		n_bins = 100
		positions = self.positions[:,0][start_time:,]
		output_rates = self.output_rates[start_time:,]
		dx = 2*self.radius / n_bins
		bin_centers = np.linspace(dx, 2*self.radius-dx, num=n_bins)
		mean_output_rates = []
		for i in np.arange(0, n_bins):
			indexing = (positions >= i*dx) & (positions < (i+1)*dx)
			mean_output_rates.append(np.mean(output_rates[indexing]))
		plt.plot(bin_centers, mean_output_rates, marker='o')
		plt.axhline(y=self.target_rate, linewidth=3, linestyle='--', color='black')

	def position_distribution(self):
		x = self.positions[:,0]
		n, bins, patches = plt.hist(x, 50, normed=True, facecolor='green', alpha=0.75)