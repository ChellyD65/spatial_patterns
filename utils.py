def rectify(value):
	"""
	Rectification of Firing Rates
	"""
	if value < 0:
		value = 0.
	return value

def rectify_array(array):
	"""
	Rectification of array entries using fancy indexing
	"""
	array[array < 0] = 0.
	return array