# fstrimmer.py
#
# Filesequence trimmer
#
# edit operations that involve trimming, such as Truncate, Trim, Absolute_trim, Head and Tail
# Takes in filesequence list and runs asked operation to each one of the seqs. If filesequence has been renamed earlier and we still carry
# reference to the original naming, these tools can duplicate the trimming operation also on the original filenames. To achieve this we need to express
# every trimming operation as absolute_trim_sequence instruction which can be run on both original and modified sequence to keep 1:1 mapping of files.

from Filesequence import Filesequence
from timecode_frame import get_frame

from math import ceil, floor
import copy

def is_single(x):
	""" Single files are passed in as strings. This check is used by edit operations that should bypass single files """
	if type(x) == str:
		return True
	else:
		return False

def get_clip_len(clip):
	""" Code dup from inside Filesequence """
	return (max(clip['start'], clip['end']) - min(clip['start'], clip['end'])) / abs(clip['increment']) + 1

def get_relative_frames(seq, head, tail):
	""" get framenumbers relative to start and end of sequence +/- frames """

	start = seq.clips[0]['start']
	end = seq.clips[-1]['end']
	direction = 1 if seq.clips[0]['increment'] >= 0 else -1
	start_frame = start + head * direction
	end_frame = end - tail * direction

	if (start_frame * direction > end_frame * direction): # too clever code checking that ends don't grow past each other
		return None, None

	return start_frame, end_frame

def absolute_trim_sequence(seq, head, tail):
	""" This is the main function in which atrim, trim, truncate, head and tail operations end up 
		It is not concerned about subclips, but trims N frames from head and tail of whole sequence.
		This opertaion should be matched with possible original sequences if multiple edits are chained to keep 1:1 mapping
		of original files to edited files """

	def chop_head(clips, n):
		""" return list with clips removed that are left under head trim of N frames """

		try:
			clip_len = get_clip_len(clips[0])
		except IndexError:
			return None

		if clip_len <= n:
			return chop_head(clips[1:], n - clip_len)

		clips[0]['start'] += n * clips[0]['increment']
		return clips

	def chop_tail(clips, n):
		""" chop n frames of tail, if whole clip is chopped proceed to next clip """

		try:
			clip_len = get_clip_len(clips[-1])
		except IndexError:
			return None
		except TypeError:
			return None

		if clip_len <= n:
			return chop_tail(clips[:-1], n - clip_len)

		clips[-1]['end'] -= n * clips[-1]['increment']
		return clips

	if head < 0: head = 0
	if tail < 0: tail = 0

	if is_single(seq): # Input is string, nothing to do early terminate
		return seq

	ret_clips = copy.deepcopy(seq.clips)
	ret_clips = chop_head(ret_clips, head)
	ret_clips = chop_tail(ret_clips, tail)

	if ret_clips:
		ret_seq = Filesequence(seq.head, ret_clips, seq.tail)
	else:
		ret_seq = None

	return ret_seq

def head_tail(seq, **kwargs):
	""" get N frames from head or tail of seq, returns instruction usable with absolute_trim_sequence """	

	def absolute_head_tail(seq, is_head, amount):
		""" Simple case of taking 'amount' frames from head or tail """
		if is_head:
			h = 0
			t = seq.frame_amount() - amount
			if t < 0: t = 0
		else:
			h = seq.frame_amount() - amount
			t = 0
			if h < 0: h = 0

		return h, t

	def relative_head_tail(seq, is_head, amount):
		""" how many frames to remove from seq, if amount refers to timecode. """
		#	We assume that person giving timecode is actually interested shortening the clip by certain time amount
		#	and whether sequence skips frames or not is not relevant 
		#	test.[0-50x2@@@@].dpx --head 25 takes 25 first filenames and becomes test.[0-48x2@@@@].dpx
		#	test.[0-50x2@@@@].dpx --head 01:00 takes one second of sequence (numbers 0-24) and becomes test.[0-24x2@@@@].dpx
		
		seq_len = max(seq.clips[-1]['end'], seq.clips[0]['start']) - min(seq.clips[0]['start'], seq.clips[-1]['end']) + 1 # Sequence length in timecode, not actual frames 

		if is_head:
			first_frame, last_frame = get_relative_frames(seq, 0, seq_len - amount)
		else:
			first_frame, last_frame = get_relative_frames(seq, seq_len - amount, 0)

		if first_frame != None and last_frame != None:
			h, t = truncate(seq, start=first_frame, end=last_frame, fps=kwargs['fps'], tc_start=0)
		else:
			h = seq.frame_amount()
			t = h

		return h, t

	is_head = kwargs['is_head']

	try:
		# We are passed frames, take literally 'amount' frames from head or tail
		amount = int(kwargs['amount'])
		return absolute_head_tail(seq, is_head, amount)

	except ValueError:
		# We are passed timecode, figure out what that means in terms of absolute frames
		amount = get_frame(kwargs['amount'], kwargs['fps'])
		return relative_head_tail(seq, is_head, amount)

def truncate(seq, **kwargs):
	""" truncate clips to absolute framerange. Everything outside start-end range will get dropped or clipped """
	start = get_frame(kwargs['start'], kwargs['fps'], kwargs['tc_start'])
	end = get_frame(kwargs['end'], kwargs['fps'], kwargs['tc_start'])	

	n = 0 # n stores length of previous clips combined
	h = seq.frame_amount() # default to trim head and tail fully
	t = seq.frame_amount()

	for clip in seq.clips:

		# Each clip can be described as line
		# frame = step * increment + offset

		offset = clip['start']
		inc = clip['increment']
		clip_len = get_clip_len(clip)

		# Solve steps where clip passes frames start and end
		t1 = ((start - offset) / float(inc))
		t2 = ((end - offset) / float(inc))

		# This is the range where t1,t2 solve and our clip overlap
		range_start = max(min(t1, t2), 0)
		range_end = min(max(t1, t2), clip_len - 1)

		# If range start and end are in logical order our clip contains frames that will survive the trimming
		# if several clips fit the bill, min() makes sure that we trim keeping as many of them as possible still in seq.
		if range_start <= range_end:
			h = min(h, n + int(ceil(range_start)))
			t = min(t, (seq.frame_amount() - 1) - (n + int(floor(range_end))))

		n += clip_len

	return h, t

def trim(seq, **kwargs):
	""" trim by 'head' and 'tail' from start and end of seq """
	
	# If we are provided with integer, input refers to amount of actual frames to trim
	# If it is timecode it means trim N seconds:frames so we need to calculate how many actual frames this means
	# in the context of this sequence as this might skip frames

	try:
		h = int(kwargs['head'])
		t = int(kwargs['tail'])

	except ValueError:		
		head = get_frame(kwargs['head'], kwargs['fps'])
		tail = get_frame(kwargs['tail'], kwargs['fps'])
		
		first_frame, last_frame = get_relative_frames(seq, head, tail)
		if first_frame != None and last_frame !=None:
			h, t = truncate(seq, start=first_frame, end=last_frame, fps=kwargs['fps'], tc_start=0)
		else:
			h = seq.frame_amount()
			t = h

	return h, t

def process_sequences(original_seqlist, modified_seqlist, trimmer, **kwargs):
	""" Figure out how much to trim each modifed sequence in list based on the provided trimmer (head, tail, trim, truncate) 
		the actual trimming is done only by absolute_trim_sequence with settings decided by said trimmer tool. 
		match the trimming of modified sequence by running original sequence through the absolute_trim_sequence as well to keep
		mapping to original filenames through multiple consecutive trimming, filtering, renaming operations """

	ret_original_seqlist = []
	ret_modified_seqlist = []

	for pair in zip(original_seqlist, modified_seqlist):
		original_seq = pair[0]
		modified_seq = pair[1]

		if not is_single(modified_seq):		
			h, t = trimmer(modified_seq, **kwargs)
		else:
			h = 0
			t = 0

		trimmed_modified = absolute_trim_sequence(modified_seq, h, t)
		if trimmed_modified:
			ret_modified_seqlist.append(trimmed_modified)
			if original_seq:
				ret_original_seqlist.append(absolute_trim_sequence(original_seq, h, t))
			else:
				ret_original_seqlist.append(None)

	return ret_original_seqlist, ret_modified_seqlist