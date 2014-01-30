import matplotlib as mpl
import math
# mpl.use('TkAgg')
import matplotlib.pyplot as plt
import numpy as np
import scipy.stats
from scipy import signal
import initialization
import general_utils.arrays
import utils
from matplotlib.collections import LineCollection
from matplotlib.colors import ListedColormap, BoundaryNorm
from mpl_toolkits.mplot3d import Axes3D

# from matplotlib._cm import cubehelix
mpl.rcParams.update({'figure.autolayout': True})
# print mpl.rcParams.keys()
# mpl.rcParams['animation.frame_format'] = 'jpeg'
# print mpl.rcParams['animation.frame_format']

def make_segments(x, y):
	'''
	Taken from http://nbviewer.ipython.org/github/dpsanders/matplotlib-examples/blob/master/colorline.ipynb

	Create list of line segments from x and y coordinates, in the correct format for LineCollection:
	an array of the form   numlines x (points per line) x 2 (x and y) array
	'''

	points = np.array([x, y]).T.reshape(-1, 1, 2)
	segments = np.concatenate([points[:-1], points[1:]], axis=1)
	
	return segments

def colorline(x, y, z=None, cmap=plt.get_cmap('gnuplot_r'), norm=plt.Normalize(0.0, 1.0), linewidth=3, alpha=1.0):
	'''
	Taken from http://nbviewer.ipython.org/github/dpsanders/matplotlib-examples/blob/master/colorline.ipynb
	
	Plot a colored line with coordinates x and y
	Optionally specify colors in the array z
	Optionally specify a colormap, a norm function and a line width
	
	Defines a function colorline that draws a (multi-)colored 2D line with coordinates x and y.
	The color is taken from optional data in z, and creates a LineCollection.

	z can be:
	- empty, in which case a default coloring will be used based on the position along the input arrays
	- a single number, for a uniform color [this can also be accomplished with the usual plt.plot]
	- an array of the length of at least the same length as x, to color according to this data
	- an array of a smaller length, in which case the colors are repeated along the curve

	The function colorline returns the LineCollection created, which can be modified afterwards.

	See also: plt.streamplot

	'''
	
	# Default colors equally spaced on [0,1]:
	if z is None:
		z = np.linspace(0.0, 1.0, len(x))
		   
	# Special case if a single number:
	if not hasattr(z, "__iter__"):  # to check for numerical input -- this is a hack
		z = np.array([z])
		
	z = np.asarray(z)
	
	segments = make_segments(x, y)
	lc = LineCollection(segments, array=z, cmap=cmap, norm=norm, linewidth=linewidth, alpha=alpha)
	
	ax = plt.gca()
	ax.add_collection(lc)
	
	return lc


def plot_list(fig, plot_list):
	"""
	Takes a list of lambda forms of plot functions and plots them such that
	no more than four rows are used to assure readability
	"""
	n_plots = len(plot_list)
	# A title for the entire figure (super title)
	# fig.suptitle('Time evolution of firing rates', y=1.1)
	for n, p in enumerate(plot_list, start=1):
		if n_plots < 4:
			fig.add_subplot(n_plots, 1, n)
			# plt.locator_params(axis='y', nbins=4)
			# plt.ylabel('firing rate')
		else:
			fig.add_subplot(math.ceil(n_plots/2.), 2, n)
			# plt.locator_params(axis='y', nbins=4)
		# ax = plt.gca()
		# if n == 1 or n == 2:
		# 	# title = r'$\sigma_{\mathrm{inh}} = %.1f $' % 0.05
		# 	# plt.title(title, y=1.02, size=26)
		# 	ax.get_xaxis().set_ticklabels([])
		# if n == 1 or n == 3:
		# 	# plt.title('Initially')
		# 	plt.ylabel('firing rate')
		# if n == 3 or n == n_plots:
		# 	# plt.title('Finally')
		# 	plt.xlabel('position')
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
		self.colors = {'exc': '#D7191C', 'inh': '#2C7BB6'}
		self.population_name = {'exc': r'excitatory', 'inh': 'inhibitory'}	
		self.populations = ['exc', 'inh']
		# self.fig = plt.figure()


	def time2frame(self, time, weight=False):
		"""Returns corresponding frame number to a given time
		
		Parameters
		----------
		- time: (float) time in the simulation
		- weight: (bool) decides wether every_nth_step or
					every_nth_step_weights is taken

		Returns
		(int) the frame number corresponding to the time
		-------
		
		"""
			
		if weight:
			every_nth_step = self.every_nth_step_weights
		else:
			every_nth_step = self.every_nth_step

		if time == -1:
			time = self.params['sim']['simulation_time']

		frame = time / every_nth_step / self.dt
		return int(frame)

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


	def plot_output_rates_via_walking(self, frame=0, spacing=201):
		"""
		DEPRECATED! Use get_output_rates_from_equation instead
		"""
		start_pos = -0.5
		end_pos = self.radius
		linspace = np.linspace(-self.radius, self.radius, spacing)
		# Initial equilibration
		equilibration_steps = 10000
		plt.xlim([-self.radius, self.radius])
		r = np.zeros(self.output_neurons)
		dt_tau = self.dt / self.tau
		# tau = 0.011
		# dt = 0.01
		# dt_tau = 0.1
		x = start_pos
		for s in np.arange(equilibration_steps):
			r = (
					r*(1 - dt_tau)
					+ dt_tau * ((
					np.dot(self.rawdata['exc']['weights'][frame],
						self.get_rates(x, 'exc')) -
					np.dot(self.rawdata['inh']['weights'][frame], 
						self.get_rates(x, 'inh'))
					)
					- self.weight_lateral
					* (np.sum(r) - r)
					)
					)
			r[r<0] = 0
		start_r = r
		print r
		output_rate = []
		for x in linspace:
			r = (
					r*(1 - dt_tau)
					+ dt_tau * ((
					np.dot(self.rawdata['exc']['weights'][frame],
						self.get_rates(x, 'exc')) -
					np.dot(self.rawdata['inh']['weights'][frame], 
						self.get_rates(x, 'inh'))
					)
					- self.weight_lateral
					* (np.sum(r) - r)
					)
					)
			r[r<0] = 0
			output_rate.append(r)
		# plt.title(start_r)
		plt.plot(linspace, output_rate)


	def rate1_vs_rate2(self, start_frame=0, three_dimensional=False, weight=0):
		target_rate = self.params['out']['target_rate']
		if three_dimensional:
			fig = plt.figure()
			ax = fig.gca(projection='3d')
			x = self.rawdata['output_rates'][start_frame:,0]
			y = self.rawdata['output_rates'][start_frame:,1]
			z = self.rawdata['inh']['weights'][start_frame:,weight,0]

			ax.plot(x, y, z)
			zlim = ax.get_zlim()
			# Plot line for target rate
			ax.plot([target_rate, target_rate],
					[target_rate, target_rate], zlim, lw=2, color='black')

			ax.set_xlabel('Rate of neuron 1')
			ax.set_ylabel('Rate of neuron 2')
			ax.set_zlabel('Weight of neuron %i' % weight)
			# ax.set_zlim(-10, 10)

			return

		else:
			plt.plot(target_rate, target_rate, marker='x', color='black', markersize=10, markeredgewidth=2)
			# plt.plot(
			# 	self.rawdata['output_rates'][start_frame:,0],
			# 	self.rawdata['output_rates'][start_frame:,1])
			x = self.rawdata['output_rates'][start_frame:,0]
			y = self.rawdata['output_rates'][start_frame:,1]
			colorline(x, y)
			# Using colorline it's necessary to set the limits again
			plt.xlim(x.min(), x.max())
			plt.ylim(y.min(), y.max())
			plt.xlabel('Output rate 1')
			plt.ylabel('Output rate 2')


		# ax = fig.gca(projection='rectilinear')


	def output_rate_vs_time(self, plot_mean=False, start_time_for_mean=0):
		"""Plot output rate of output neurons vs time
		
		Parameters
		----------
		- plot_mean: (boolian) If True the mean is plotted as horizontal line
		- start_time_for_mean: (float) The time from which on the mean is to
								be taken
		"""
			
		plt.xlabel('Time')
		plt.ylabel('Output rates')
		time = general_utils.arrays.take_every_nth(self.time, self.every_nth_step)		
		plt.plot(time, self.rawdata['output_rates'])
		plt.axhline(self.target_rate, lw=4, ls='dashed', color='black', 
					label='Target', zorder=3)
		if plot_mean:
			start_frame = self.time2frame(start_time_for_mean)
			# print start_frame
			mean = np.mean(self.rawdata['output_rates'][start_frame:], axis=0)
			legend = 'Mean:' + str(mean)
			plt.hlines(mean, xmin=start_time_for_mean, xmax=max(time), lw=4,
						color='red', label=legend, zorder=4)

		plt.legend(bbox_to_anchor=(1, 1), loc='upper right', fontsize=8)

			# plt.axhline(mean[1], xmin=start_frame)
			# print mean

	def output_rates_vs_position(self, start_frame=0, clipping=False):
		if self.dimensions == 1:
			_positions = self.positions[:,0][start_frame:,]
			_output_rates = self.output_rates[start_frame:,]
			plt.plot(_positions, _output_rates, linestyle='none', marker='o', alpha=0.5)
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
		# ax = plt.gca()
		# ax.set_aspect('equal')
		# ax.set_xticks([])
		# ax.set_yticks([])

	def plot_sigmas_vs_centers(self):
		for t in ['exc', 'inh']:
			plt.plot(self.rawdata[t]['centers'], self.rawdata[t]['sigmas'],
				color=self.colors[t], marker='o', linestyle='none')

	def plot_sigma_distribution(self):
		if self.params['inh']['sigma_distribution'] == 'cut_off_gaussian':
			plt.xlim(0, self.params['inh']['sigma_spreading']['right'])
			for t in ['exc', 'inh']:
				plt.hist(self.rawdata[t]['sigmas'], bins=10, color=self.colors[t])
		else:
			# plt.xlim(0, )
			for t in ['exc', 'inh']:
				plt.hist(self.rawdata[t]['sigmas'], bins=10, color=self.colors[t])

	def get_rates(self, position, syn_type):
		"""
		Computes the values of all place field Gaussians at <position>

		Inherited from Synapses
		"""
		get_rates = self.get_rates_function(position, data=self.rawdata[syn_type])
		# return self.set_rates(position, data=self.rawdata[syn_type])
		return get_rates(position)


	def get_output_rate(self, position, frame):
		"""
		Note: if you want it for several times don't calculate set_rates every time, because it does not change!!!
		"""
		if self.lateral_inhibition:
			start_pos = -0.5
			end_pos = self.radius
			# Initial equilibration
			equilibration_steps = 10000
			plt.xlim([-self.radius, self.radius])
			r = np.zeros(self.output_neurons)
			dt_tau = self.dt / self.tau
			# tau = 0.011
			# dt = 0.01
			# dt_tau = 0.1
			x = start_pos
			for s in np.arange(equilibration_steps):
				r = (
						r*(1 - dt_tau)
						+ dt_tau * ((
						np.dot(self.rawdata['exc']['weights'][frame],
							self.get_rates(x, 'exc')) -
						np.dot(self.rawdata['inh']['weights'][frame], 
							self.get_rates(x, 'inh'))
						)
						- self.weight_lateral
						* (np.sum(r) - r)
						)
						)
				r[r<0] = 0
			start_r = r
			print r
			output_rates = []
			for x in linspace:
				r = (
						r*(1 - dt_tau)
						+ dt_tau * ((
						np.dot(self.rawdata['exc']['weights'][frame],
							self.get_rates(x, 'exc')) -
						np.dot(self.rawdata['inh']['weights'][frame], 
							self.get_rates(x, 'inh'))
						)
						- self.weight_lateral
						* (np.sum(r) - r)
						)
						)
				r[r<0] = 0
				output_rates.append(r)


		else:
			output_rate = (
				np.dot(self.rawdata['exc']['weights'][frame],
				 self.get_rates(position[0], 'exc')) 
				- np.dot(self.rawdata['inh']['weights'][frame],
				 self.get_rates(position[0], 'inh')) 
			)
		return output_rate
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
		# if self.boxtype == 'circular':
		# 	distance = np.sqrt(X*X + Y*Y)
		# 	positions_grid[distance>self.radius] = np.nan
		rates_grid['exc'] = self.get_rates(positions_grid, 'exc')
		rates_grid['inh'] = self.get_rates(positions_grid, 'inh')
		return X, Y, positions_grid, rates_grid

	def get_output_rates_from_equation(self, frame, spacing,
				positions_grid=False, rates_grid=False,
				equilibration_steps=10000):
		"""
		Return output_rates at many positions
		
		For normal plotting in 1D and for contour plotting in 2D.
		It is differentiated between cases with and without lateral inhibition.

		With lateral inhibition the output rate has to be determined via
		integration (but fixed weights).
		In 1 dimensions we start at one end of the box, integrate for a
		time specified by equilibration steps and than walk to the 
		other end of the box.
		In 2 dimensions ...

		ARGUMENTS:
		- frame: frame at which the output rates are plotted 
		- spacing: the spacing, describing the detail richness of the plor or contour plot (spacing**2)
		- positions_grid, rates_grid: Arrays as described in get_X_Y_positions_grid_rates_grid_tuple
		- equilibration steps number of steps of integration to reach the
		 	correct value of the output rates for the case of lateral inhibition

		"""
		# plt.title('output_rates, t = %.1e' % (frame * self.every_nth_step_weights), fontsize=8)

		if self.dimensions == 1:
			linspace = np.linspace(-self.radius, self.radius, spacing)

			if self.lateral_inhibition:
				output_rates = np.empty((spacing, self.output_neurons))
			
				start_pos = -self.radius
				end_pos = self.radius
				linspace = np.linspace(-self.radius, self.radius, spacing)
				plt.xlim([-self.radius, self.radius])
				r = np.zeros(self.output_neurons)
				dt_tau = self.dt / self.tau
				# tau = 0.011
				# dt = 0.01
				# dt_tau = 0.1
				x = start_pos
				for s in np.arange(equilibration_steps):
					r = (
							r*(1 - dt_tau)
							+ dt_tau * ((
							np.dot(self.rawdata['exc']['weights'][frame],
								self.get_rates(x, 'exc')) -
							np.dot(self.rawdata['inh']['weights'][frame], 
								self.get_rates(x, 'inh'))
							)
							- self.weight_lateral
							* (np.sum(r) - r)
							)
							)
					r[r<0] = 0
				start_r = r
				# print r
				# output_rates = []
				for n, x in enumerate(linspace):
					r = (
							r*(1 - dt_tau)
							+ dt_tau * ((
							np.dot(self.rawdata['exc']['weights'][frame],
								self.get_rates(x, 'exc')) -
							np.dot(self.rawdata['inh']['weights'][frame], 
								self.get_rates(x, 'inh'))
							)
							- self.weight_lateral
							* (np.sum(r) - r)
							)
							)
					r[r<0] = 0
					output_rates[n] = r

			else:
				output_rates = np.empty(spacing)
				for n, x in enumerate(linspace):
					output_rates[n] = self.get_output_rate([x, None], frame)
				output_rates[output_rates < 0] = 0.
			
			return linspace, output_rates

		if self.dimensions == 2:
			if self.lateral_inhibition:
				output_rates = np.empty((spacing, spacing, self.output_neurons))
				start_pos = positions_grid[0, 0, 0, 0]
				r = np.zeros(self.output_neurons)
				dt_tau = self.dt / self.tau

				pos = start_pos
				for s in np.arange(equilibration_steps):
					r = (
							r*(1 - dt_tau)
							+ dt_tau * ((
							np.dot(self.rawdata['exc']['weights'][frame],
								self.get_rates(pos, 'exc')) -
							np.dot(self.rawdata['inh']['weights'][frame], 
								self.get_rates(pos, 'inh'))
							)
							- self.weight_lateral
							* (np.sum(r) - r)
							)
							)
					r[r<0] = 0
				# start_r = r
				# print r
				# output_rates = []

				for ny in np.arange(positions_grid.shape[1]):
					for nx in nx_list:
						pos = positions_grid[nx][ny]
						for s in np.arange(100):
							r = (
									r*(1 - dt_tau)
									+ dt_tau * ((
									np.dot(self.rawdata['exc']['weights'][frame],
										self.get_rates(pos, 'exc')) -
									np.dot(self.rawdata['inh']['weights'][frame], 
										self.get_rates(pos, 'inh'))
									)
									- self.weight_lateral
									* (np.sum(r) - r)
									)
									)
							r[r<0] = 0

						output_rates[nx][ny] = r

				for i in np.arange(self.output_neurons):
					output_rates[:,:,i] = np.transpose(output_rates[:,:,i])

			else:
				output_rates = np.empty((spacing, spacing))
				# Note how the tensor dot product is used
				output_rates = (
					np.tensordot(self.rawdata['exc']['weights'][frame],
										rates_grid['exc'], axes=([0], [2]))
					- np.tensordot(self.rawdata['inh']['weights'][frame],
						 				rates_grid['inh'], axes=([0], [2]))
				)
				# Transposing is necessary for the contour plot
				output_rates = np.transpose(output_rates)
				# Rectification
				output_rates[output_rates < 0] = 0.
			return output_rates		

	def output_rate_heat_map(
			self, start_time=0, end_time=-1, spacing=101, maximal_rate=False, 
			number_of_different_colors=50, equilibration_steps=10000):
		"""Plot evolution of output rate from equation vs time

		Time is the vertical axis. Linear space is the horizontal axis.
		Output rate is given in color code.
		
		Parameters
		----------
		- start_time, end_time: (int) determine the time range
		- spacing: (int) resolution along the horizontal axis
						(note: the resolution along the vertical axis is given
							by the data)
		- maximal_rate: (float) Above this value everything is plotted in black.
 						This is useful if smaller values should appear in
 						more detail. If left as False, the largest appearing
 						value of all occurring output rates is taken.
 		- number_of_different_colors: (int) Number of colors used for the
 											color coding
		"""
			
		lateral_inhibition = self.params['sim']['lateral_inhibition']
		fig = plt.figure()
		fig.set_size_inches(6, 3.5)
		# fig.set_size_inches(6, 3.5)
		first_frame = self.time2frame(start_time, weight=True)
		last_frame = self.time2frame(end_time, weight=True)
		if lateral_inhibition:
			output_rates = np.empty((last_frame-first_frame+1,
							spacing, self.params['sim']['output_neurons']))
		else:
			output_rates = np.empty((last_frame-first_frame+1, spacing))
		frames = np.arange(first_frame, last_frame+1)
		for i in frames:
			linspace, output_rates[i-first_frame] = (
					self.get_output_rates_from_equation(
						i, spacing=spacing, equilibration_steps=equilibration_steps))
			print 'frame: %i' % i
		time = frames * self.every_nth_step_weights
		X, Y = np.meshgrid(linspace, time)
		# color_norm = mpl.colors.Normalize(0., 50.)
		if not maximal_rate:
			maximal_rate = int(np.ceil(np.amax(output_rates)))
		V = np.linspace(0, maximal_rate, number_of_different_colors)
		plt.ylabel('time')
		plt.xlabel('position')
		if lateral_inhibition:
			cm_list = [mpl.cm.Blues, mpl.cm.Greens, mpl.cm.Reds, mpl.cm.Greys]
			cm = mpl.cm.Blues
			for n in np.arange(int(self.params['sim']['output_neurons'])):
				cm = cm_list[n]
				my_masked_array = np.ma.masked_equal(output_rates[...,n], 0.0)
				plt.contourf(X, Y, my_masked_array, V, cmap=cm, extend='max')
		else:
			cm = mpl.cm.gnuplot_r
			plt.contourf(X, Y, output_rates, V, cmap=cm, extend='max')
		cm.set_over('black', 1.0) # Set the color for values higher than maximum
		cm.set_bad('white', alpha=0.0)

		# plt.contourf(X, Y, output_rates, V, cmap=cm)
		ax = plt.gca()
		plt.ticklabel_format(axis='y', style='sci', scilimits=(0, 0))
		plt.locator_params(axis='y', nbins=5)
		ax.invert_yaxis()
		cb = plt.colorbar()
		cb.set_label('firing rate')



	def plot_output_rates_from_equation(self, time, spacing=101, fill=False, correlogram=False):
		"""Plots output rates or correlograms using the weights
		
		Correlogram:
		The correlogram is obtained by using signal.correlate or 
		signal.correlate2d.
		For 2D we normalize the correlation array. It works as follows:
		The autocorrelation array is obtained by taking two rate maps and
		moving them with respect to each other and measuren the extent of
		rate overlap. The two rate maps can be moved in the interval (-2r, +2r).
		To normalize the result, we divide each data point in the correlation
		map by the number of overlapping points in that data point.
		To this end we create an array that contains the number of overlapping
		squares for reach data point. See also the Evernote notes on
		Correlograms.

		Parameters
		----------
		- frame: (int) Frame of the simulation that shall be plotted
		- spacing: (int) The output will contain spacing**dimensions data points
		- fill: (boolean) If True the contour plot will be filled, if False
							it will be just lines
		- correlogram: (boolean) If True the correlogram instead of the output
								rates will be plotted

		Returns
		-------
		
		"""
		frame = self.time2frame(time, weight=True)	
		if self.dimensions == 1:
			# fig = plt.figure()
			linspace, output_rates = self.get_output_rates_from_equation(frame, spacing)

			if correlogram:
				correlation = signal.correlate(output_rates, output_rates, mode='full')
				plt.plot(correlation)

			else:
				plt.xlim(-self.radius, self.radius)
				# color='#FDAE61'
				plt.plot(linspace, output_rates, lw=2)
				# title = 'time = %.0e' % (frame*self.every_nth_step_weights)
				# plt.title(title, size=16)
				plt.locator_params(axis='y', nbins=2)
				# plt.xlabel('position')
				plt.ylabel('firing rate')
				# fig.set_size_inches(5,2)

		if self.dimensions == 2:
			# X, Y, output_rates = self.get_output_rates_from_equation(frame, spacing)
			X, Y, positions_grid, rates_grid = self.get_X_Y_positions_grid_rates_grid_tuple(spacing)
			output_rates = self.get_output_rates_from_equation(frame, spacing, positions_grid, rates_grid)
			# Hack to avoid error in case of vanishing output rate at every position
			# If every entry in output_rates is 0, you define a norm and set
			# one of the elements to a small value (such that it looks like zero)			
			# title = r'$\vec \sigma_{\mathrm{inh}} = (%.2f, %.2f)$' % (self.params['inh']['sigma_x'], self.params['inh']['sigma_y'])
			# plt.title(title, y=1.04, size=36)
			title = 't=%.2e' % time
			plt.title(title)
			cm = mpl.cm.jet
			cm.set_over('y', 1.0) # Set the color for values higher than maximum
			cm.set_bad('white', alpha=0.0)
			# V = np.linspace(0, 3, 20)
			V = 20
			if correlogram:
				# Create the normalization array of the correlogram
				correlations_shape = (2*spacing-1, 2*spacing-1)
				normalization = np.empty(correlations_shape)
				for i in np.arange(-spacing+1, spacing):
					for j in np.arange(-spacing+1, spacing):
						normalization[i+spacing-1][j+spacing-1] = (spacing-abs(i))*(spacing-abs(j))
			if fill:
				# if np.count_nonzero(output_rates) == 0 or np.isnan(np.max(output_rates)):
				if np.count_nonzero(output_rates) == 0:
					color_norm = mpl.colors.Normalize(0., 100.)
					output_rates[0][0] = 0.000001
					plt.contourf(X, Y, output_rates[...,0], V, norm=color_norm, cmap=cm, extend='max')
				else:
					if self.lateral_inhibition:
						# plt.contourf(X, Y, output_rates[:,:,0], V, cmap=cm, extend='max')
						cm_list = [mpl.cm.Blues, mpl.cm.Greens, mpl.cm.Reds, mpl.cm.Greys]
						# cm = mpl.cm.Blues
						for n in np.arange(int(self.params['sim']['output_neurons'])):
							cm = cm_list[n]
							my_masked_array = np.ma.masked_equal(output_rates[...,n], 0.0)
							plt.contourf(X, Y, my_masked_array, V, cmap=cm, extend='max')
					else:
						plt.contourf(X, Y, output_rates, V, cmap=cm, extend='max')					
			else:
				if np.count_nonzero(output_rates) == 0:
					color_norm = mpl.colors.Normalize(0., 100.)
					output_rates[0][0] = 0.000001
					if self.boxtype == 'circular':
						distance = np.sqrt(X*X + Y*Y)
						output_rates[distance>self.radius] = np.nan
					plt.contour(X, Y, output_rates, V, norm=color_norm, cmap=cm, extend='max')
				else:
					if correlogram:
						correlations = signal.correlate2d(output_rates, output_rates)
						x_space_corr = np.linspace(-2*self.radius, 2*self.radius, 2*spacing-1)
						y_space_corr = np.linspace(-2*self.radius, 2*self.radius, 2*spacing-1)
						X_corr, Y_corr = np.meshgrid(x_space_corr, y_space_corr)
						if self.boxtype == 'circular':
							distance = np.sqrt(X_corr*X_corr + Y_corr*Y_corr)
							correlations[distance>2*self.radius] = np.nan						
						plt.contour(X_corr, Y_corr, correlations/normalization, cmap=cm)
					else:
						if self.boxtype == 'circular':
							distance = np.sqrt(X*X + Y*Y)
							output_rates[distance>self.radius] = np.nan	
						if self.lateral_inhibition:
							plt.contour(X, Y, output_rates[:,:,0], V, cmap=cm, extend='max')
						else:
							plt.contour(X, Y, output_rates, V, cmap=cm, extend='max')
			cb = plt.colorbar()
			cb.set_label('firing rate')
			ax = plt.gca()
			if self.boxtype == 'circular':
				# fig = plt.gcf()
				# for item in [fig, ax]:
				# 	item.patch.set_visible(False)
				ax.axis('off')
				circle1=plt.Circle((0,0),.497, ec='black', fc='none', lw=2)
				ax.add_artist(circle1)
			if self.boxtype == 'linear':
				rectangle1=plt.Rectangle((-self.radius, -self.radius),
						2*self.radius, 2*self.radius, ec='black', fc='none', lw=2)
				ax.add_artist(rectangle1)
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

	def fields(self, show_each_field=True, show_sum=False, neuron=0):
		"""
		Plotting of Gaussian Fields and their sum

		Note: The sum gets divided by a something that depends on the 
				number of cells of the specific type, to make it fit into
				the frame (see note in fields_times_weighs)
		"""
		x = self.box_linspace
		# Loop over different synapse types and color tuples
		plt.xlim([-self.radius, self.radius])
		plt.xlabel('position')
		plt.ylabel('firing rate')
		# plt.title('firing rate of')
		for t in self.populations:
			title = '%i fields per synapse' % len(self.rawdata[t]['centers'][neuron])
			# plt.title(title)
			legend = self.population_name[t]
			summe = 0
			for c, s in np.nditer([self.rawdata[t]['centers'][neuron], self.rawdata[t]['sigmas'][neuron]]):
				gaussian = scipy.stats.norm(loc=c, scale=s).pdf
				if show_each_field:
					plt.plot(x, gaussian(x), color=self.colors[t])
				summe += gaussian(x)
			# for c, s in np.nditer([self.rawdata[t]['centers'][5], self.rawdata[t]['sigmas'][5]]):
			# 	gaussian = scipy.stats.norm(loc=c, scale=s).pdf
			# 	if show_each_field:
			# 		plt.plot(x, gaussian(x), color=self.colors[t], label=legend)
			# 	summe += gaussian(x)     
			if show_sum:
				plt.plot(x, summe, color=self.colors[t], linewidth=4, label=legend)
			plt.legend(bbox_to_anchor=(1, 1), loc='upper right')
		return

	def weights_vs_centers(self, syn_type='exc', frame=-1):
		"""Plots the current weight at each center"""
			
		plt.title(syn_type + ' Weights vs Centers' + ', ' + 'Frame = ' + str(frame), fontsize=8)	
		plt.xlim(-self.radius, self.radius)
		centers = self.rawdata[syn_type]['centers']
		weights = self.rawdata[syn_type]['weights'][frame]
		plt.plot(centers, weights, color=self.colors[syn_type], marker='o')

	def weight_evolution(self, syn_type='exc', time_sparsification=1,
						 weight_sparsification=1, output_neuron=0):
		"""
		Plots the time evolution of synaptic weights.

		The case of multiple output neurons needs to be treated separately
		----------
		Arguments:
		- syn_type: type of the synapse
		- time_sparsification: factor by which the time resolution is reduced
		- weight_sparsification: factor by which the number of weights
									is reduced

		----------
		Remarks:
		- If you use an already sparsified weight array as input, the center
			 color-coding won't work
		"""

		syn = self.rawdata[syn_type]
		plt.title(syn_type + ' weight evolution', fontsize=8)
		# Create time array, note that you need to add 1, because you also
		# have time 0.0
		time = np.linspace(
			0, self.simulation_time,
			num=(self.simulation_time / time_sparsification
				/ self.every_nth_step_weights + 1))
		# Loop over individual weights (using sparsification)
		# Note the arange takes as an (excluded) endpoint the length of the
		# first weight array
		# assuming that the number of weights is constant during the simulation
		if not self.params['sim']['lateral_inhibition']:
			for i in np.arange(0, len(syn['weights'][0]), weight_sparsification):
				# Create array of the i-th weight for all times
				weight = syn['weights'][:,i]
				center = syn['centers'][i]
				# Take only the entries corresponding to the sparsified times
				weight = general_utils.arrays.take_every_nth(
							weight, time_sparsification)	
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
		else:
			for i in np.arange(0, self.params[syn_type]['n'],
								 weight_sparsification):
				weight = syn['weights'][:,output_neuron,i]
				center = syn['centers'][i]
				weight = general_utils.arrays.take_every_nth(weight,
				 			time_sparsification)

		plt.plot(weight)

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