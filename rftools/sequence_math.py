# sequence_math.py
#
# helper functions to do combining operations to sequences

from Filesequence import Filesequence
from fractions import Fraction

def compare_seqs(a, b):
	""" return true if a and b are part of the same seq 
		eats problems caused by strings or None sequenses """

	try:
		if (a.head == b.head) and (a.tail == b.tail):
			return True
		else:
			return False
	except AttributeError:
		return False


def merge(a, b):
	""" take in two sequences and return combined version if they fit together
		eats errors incase of 'None' input or strings """

	ret = Filesequence("", [], "")

	if compare_seqs(a, b):
			ret.head = a.head
			ret.tail = b.tail

			ret.clips = a.clips + b.clips

			return ret
	else:
		return None

def sequence_cover(a):
	""" takes in sequence and creates one continous sequence which covers that area
		if sequence has clips with different paddings, those are considered separate areas """

	def find_ends(clips):
		""" get max and min point of each different padding, returns two dicts """ 
		min_start = {}
		max_end = {}
		orientation = 0 

		for clip in clips:
			orientation += 1 if clip['increment'] >= 0 else -1 # Keep statistics on which direction most of the clips go
			padding = clip['padding']
			low_point, high_point = get_clip_low_high(clip)
			if not padding in min_start:
				min_start[padding] = low_point
				max_end[padding] = high_point
			else:
				if min_start[padding] > low_point:
					min_start[padding] = low_point
				if max_end[padding] < high_point:
					max_end[padding] = high_point
			
		if orientation >= 0: 
			direction = 1
		else:
			direction = -1

		return min_start, max_end, direction

	try:
		clips = a.clips
	except AttributeError:
		return a # input might be single file brought in as string

	ret = Filesequence(a.head,[],a.tail)
	min_start, max_end, direction = find_ends(clips)

	for padding in min_start:
		ret_clip = {}
		ret_clip['padding'] = padding
		ret_clip['start'] = min_start[padding]
		ret_clip['end'] = max_end[padding]
		ret_clip['increment'] = direction

		ret.clips.append(ret_clip)

	return ret

def reverse_clip(a):
	""" change direction of clip """
	inc = -1 * int(a['increment'])
	return {'start': a['end'], 'end': a['start'], 'increment': inc, 'padding': a['padding']}

def invert(a):
	""" gives back sequences that are inside the area covered by a, but not included in the sequence 
		basicly just taking cover of a and substracting a itself from it """

	return substract(sequence_cover(a), a)

def get_clip_low_high(c):
	""" return the low end and high end of clip without regrads to it's direction """
	low = min(c['start'], c['end'])
	high = max(c['start'], c['end'])

	return low, high

def get_offset(a, b):
	""" figure at what point b is in it's incerements where a starts """
	a_low, a_high = get_clip_low_high(a)
	b_low, b_high = get_clip_low_high(b)

	start = max(a_low, b_low)
	end = min(a_high, b_high)

	offset = (start - b_low) % b['increment']

	return offset

def substract_clips(a, b, offset):
	""" take b away from a """
	def create_mini_clip(proto, start, length):
		return {'start': start, 'end': start + (length-1), 'increment': 1, 'padding': proto['padding']}

	def chop_clip(a, b):
		""" make sure a is no longer than b """
		if a['start'] < b['start']: a['start'] = b['start']
		if a['end'] > b['end']: a['end'] = b['end']

		return a

	clip_list = []

	b_stepping = Fraction(1, abs(b['increment']))
	new_inc = 1 - b_stepping
	if new_inc == 0: return []

	clip_len = new_inc.numerator
	hop = new_inc.denominator
	start = a['start'] - offset + 1
	while start <= a['end']:
		new_clip = create_mini_clip(b, start, clip_len)
		new_clip = chop_clip(new_clip, a)
		clip_list.append(new_clip)
		start += hop

	return clip_list

def handle_under(a,b):
	""" a is under b, we need to check if B is sequence with stepping and possibly puncture A in to smaller clips
		For example if b is [0-12x4] and a is [0-12] return [1-3,5-7,9-11]"""
	offset = get_offset(a, b) # Figure out at what step B clip is on when A starts
	punctured_clips = substract_clips(a, b, offset)
	return punctured_clips

def splitter(a, b_list):
	""" Recursive splitter, that checks overlap of B's head against A and recurses further if needed """

	# End of B, break recursion
	try:
		b = b_list[0]
	except IndexError:
		return [a]

	ret_a = []

	if b['padding'] != a['padding']: 
		ret_a += splitter(a, b_list[1:])
		return ret_a

	a_low, a_high = get_clip_low_high(a)
	b_low, b_high = get_clip_low_high(b)	

	# A and B don't overlap
	# <--- a --->
	#             <----- b ----->
	if (a_low < b_low and a_high < b_high) or (a_low > b_low and a_high > b_high): 
		ret_a += splitter(a, b_list[1:])
		return ret_a

	# A is fully under B
	#        <------- a ------>
	# <-------------- b ------------->
	if a_low >= b_low and a_high <= b_high:
		ret_a += handle_under(a, b)

		return ret_a

	# B is fully under A
	# <-------------- a -------------->
	#        <------- b ------->

	if a_low < b_low and a_high > b_high:
		out1 = {'start': a_low, 'end': b_low - 1, 'increment': 1, 'padding': a['padding']}
		out2 = {'start': b_high + 1, 'end': a_high, 'increment': 1, 'padding': a['padding']}

		in1 = {'start': b_low, 'end': b_high, 'increment': 1, 'padding': a['padding']}

		# Divide A in two and recurse further
		ret_a += splitter(out1, b_list[1:])
		ret_a += handle_under(in1, b)		
		ret_a += splitter(out2, b_list[1:])


		return ret_a

	# A is lower than B
	# <------- a -------->
	#             <--------- b ------>

	if a_high >= b_low and a_high <= b_high:
		out1 = {'start': a_low, 'end': b_low - 1, 'increment': 1, 'padding': a['padding']}
		ret_a += splitter(out1, b_list[1:])

		in1 = {'start': b_low, 'end': a_high, 'increment': 1, 'padding': a['padding']}
		ret_a += handle_under(in1, b)

		return ret_a

	# A is higher than B
	#             <--------- a -------->
	# <--------- b ------->

	if a_low >= b_low and a_low <= b_high:

		in1 = {'start': a_low, 'end': b_high, 'increment': 1, 'padding': a['padding']}
		ret_a += handle_under(in1, b)

		out1 = {'start': b_high + 1, 'end': a_high, 'increment': 1, 'padding': a['padding']}
		ret_a += splitter(out1, b_list[1:])

		return ret_a


def substract(a, b):
	""" take away b clips from a clips """

	if not compare_seqs(a,b): return a

	ret_clips = []
	for a_clip in a.clips:

		splitted_clips = splitter(a_clip,b.clips)
		if a_clip['increment'] < 0: splitted_clips = map(reverse_clip, splitted_clips[::-1])
		ret_clips += splitted_clips

	if ret_clips:
		return Filesequence(a.head, ret_clips, a.tail)
	else:
		return None