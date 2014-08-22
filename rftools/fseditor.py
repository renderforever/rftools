"""
The editing engine called by fsedit

Take in Filesequence objects, desired manipulation and return 'original -> modified' filesequence objects back


"""

from timecode_frame import get_frame
from Filesequence import Filesequence
import fstrimmer
import sequence_math
import copy
import re
import collections

def is_single(x):
	""" Single files are passed in as strings. This check is used by edit operations that should bypass single files """
	if type(x) == str:
		return True
	else:
		return False

def offset(seqlist, **kwargs):

	def offset_each(seq, amount):
		""" simple offset by X frames """
		def offset_clip(clip, amount):
			clip['start'] += amount
			clip['end'] += amount
			return clip
		ret_seq = copy.deepcopy(seq)
		try:
			ret_seq.clips = map(offset_clip, ret_seq.clips, [amount] * len(ret_seq.clips))
		except AttributeError:
			pass
		return ret_seq

	def calculate_offset(new, old):
		return new - old

	def offset_based_on_start(seqlist, new_start):
		ret = []
		for seq in seqlist:
			try:
				amount = calculate_offset(new_start, seq.clips[0]['start'])
				ret.append(offset_each(seq, amount))
			except AttributeError:
				ret.append(seq)

		return ret

	def offset_based_on_end(seqlist, new_end):
		ret = []
		for seq in seqlist:
			try:
				amount = calculate_offset(new_end, seq.clips[-1]['end'])
				ret.append(offset_each(seq, amount))
			except AttributeError:
				ret.append(seq)

		return ret

	ret_seqs = []

	if kwargs.has_key('amount'):
		# Simple offset by amount
		amount = get_frame(kwargs['amount'], kwargs['fps'], kwargs['tc_start'])
		ret_seqs = map(offset_each, seqlist, [amount] * len(seqlist))
	else:
		if kwargs.has_key('start_at'):
			ret_seqs = offset_based_on_start(seqlist, get_frame(kwargs['start_at'], kwargs['fps'], kwargs['tc_start']))
		if kwargs.has_key('end_at'):
			ret_seqs = offset_based_on_end(seqlist, get_frame(kwargs['end_at'], kwargs['fps'], kwargs['tc_start']))

	return ret_seqs

def basename(seqlist, **kwargs):

	ret_seqs = []
	for seq in seqlist:
		if not is_single(seq):
			if kwargs['headname'] != "-":
				headname = kwargs['headname']
			else:
				headname = seq.head

			if kwargs['tailname'] != "-":
				tailname = kwargs['tailname']
			else:
				tailname = seq.tail

			ret_seqs.append(Filesequence(headname, seq.clips, tailname))
		else:
			ret_seqs.append(seq)

	return ret_seqs


def padding(seqlist, **kwargs):
	amount = kwargs['amount']

	def update_padding(seq, amount):
		ret_seq = copy.deepcopy(seq) # Create copy to limit side effects to inside this function
		if is_single(seq): return ret_seq

		for clip in ret_seq.clips:
			clip['padding'] = amount
		return ret_seq

	return map (update_padding, seqlist, [amount] * len(seqlist))

def reconstruct(seqlist, **kwargs):
	""" rename / merge sequences from seqlist taking naming from the 'to' seq """

	to_seq = kwargs['to'] # Turn our seqlist in to segments of this
	to_seq_frame_amount = to_seq.frame_amount()
	
	head = 0
	trimmed_seqs = []
	for seq in seqlist:
		# Roll through each sequence, measure it's length and chop our to_seq to corresponding pieces
		# iterative approach, could be recursive as well?
		if is_single(seq):
			frame_amount = 1
		else:
			frame_amount = seq.frame_amount()
		
		h, t = fstrimmer.trim(to_seq, head=head, tail=to_seq_frame_amount - (frame_amount + head), fps=None)
		trim_seq = fstrimmer.absolute_trim_sequence(to_seq, h, t)

		if trim_seq: trimmed_seqs.append(trim_seq)
		head += frame_amount

	return filter(lambda seq: seq.clips != [], trimmed_seqs) # Once again trim empty clips out from seq

def remove_gaps(seqlist):
	""" Make seq increment of 1 with the length of the sequence """
	def remove_seq_gaps(seq):
		# gapless sequence, starts like sequence clip[0], and goes to same direction (increment of -1 or 1) for the length of original
		if is_single(seq): return seq
		frame_amount = seq.frame_amount()
		increment = 1 if seq.clips[0]['increment'] > 0 else -1
		start = seq.clips[0]['start']
		end = start + ((frame_amount - 1) * increment)
		padding = seq.clips[0]['padding']
		new_clips = [{'start': start, 'end': end, 'padding': padding,'increment': increment}]
		return Filesequence(seq.head, new_clips, seq.tail)

	return map (remove_seq_gaps, seqlist)

def reverse(seqlist):

	ret = []

	for seq in seqlist:
		if is_single(seq):
			ret.append(seq)
		else:
			ret_clips = list(reversed(map(sequence_math.reverse_clip, seq.clips)))
			ret.append(Filesequence(seq.head, ret_clips, seq.tail))

	return ret
 
def maxseq(original_seqlist, modified_seqlist, **kwargs):
	amount = get_frame(kwargs['amount'], kwargs['fps'])
	ret_original = []
	ret_modified = []

	for pair in zip(original_seqlist, modified_seqlist):
		if is_single(pair[1]):
			ret_original.append(pair[0])
			ret_modified.append(pair[1])
		else:
			if pair[1].frame_amount() <= amount:
				ret_original.append(pair[0])
				ret_modified.append(pair[1])

	return ret_original, ret_modified

def minseq(original_seqlist, modified_seqlist, **kwargs):
	amount = get_frame(kwargs['amount'], kwargs['fps'])
	if amount <= 1: return original_seqlist, modified_seqlist # Early terminate for short min limit

	clean_list = filter(lambda pair: not is_single(pair[1]), zip(original_seqlist, modified_seqlist)) # Purge nonsequence items
	long_seqs = filter(lambda pair: pair[1].frame_amount() >= amount, clean_list)

	if long_seqs != []:
		return zip(*long_seqs)
	else:
		return [], []

def reorder(seqlist, **kwargs):
	def check_bounds(i, min, max):
		if (i < min) or (i > max):
			raise IndexError ("No sequence at location " + str(i))

	def interpret_order_string(cell, max_len):
		""" reorder reads instructions that are given in the following format:
			single clips are comma separated "1,3,2" (change order of clips 3 and 2)
			Range can be defined "10-1" (reorder clips reverse from 10 to 1)
			Range can be open ended "-3, 5, 4, 6-" (flip 5 and 4, keep rest of the seqlist as is) 
			(Support for looping?)
			"""
		try:
			ret = int(cell)
			if ret <= 0:
				ret = cell  # -3, is a range, not a negative value
			else:
				check_bounds(ret, 1, max_len)		
		except ValueError:
			ret = cell

		if ret == cell: # cell stayed as string, translate it to ints
			valid = re.findall('[\d]|-', ret) # Strip all the other except [0-9] and -
			if valid[0] == '-': valid = ['1'] + valid # If cell is of the format -3 append omitted 1
			if valid[-1] == '-': valid.append(str(max_len)) # if cell is of the format 4- terminate to max len
			valid_str = ''.join(valid).split('-') # Concatenate valid list to string and split it from '-'

			if len(valid_str) != 2: raise ValueError("'" + cell + "' not valid reorder instruction")
			start = int(valid_str[0])
			end = int(valid_str[1])

			check_bounds(start, 1, max_len)
			check_bounds(end, 1, max_len)

			ret = range(start, end + 1) if start < end else range(start, end - 1, -1)

		return ret

	def flatten(l):
	    for el in l:
	        if isinstance(el, collections.Iterable) and not isinstance(el, basestring):
	            for sub in flatten(el):
	                yield sub
	        else:
	            yield el

	order_string = kwargs['order_string']
	order_list = order_string.split(',')
	interpreted_list = map(interpret_order_string, order_list, [len(seqlist)] * len(order_list))
	flat_list = flatten(interpreted_list)

	# Construct reordered sequence by substituting each instruction in flatlist with correspondig seq from seqlist
	ret_list = map(lambda i: seqlist[(i-1)], flat_list)

	return ret_list