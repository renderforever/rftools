# fsoutformat.py
#
# Takes in filesequence object and returns it out in style
# These styles have been matched to take same number of parameters (2), so that we can pass them as variables in parent function (fsformat)
# Most of them need only one so the parameter is called unused

from Filesequence import Filesequence
from timecode_frame import get_timecode
import re

def straight_style(seq, **kwargs):
	return [seq]

def printf_style(seq, **kwargs):

	ret = []

	for clip in seq.clips:
		ret.append(seq.head + "%0" + str(clip['padding']) + "d" + seq.tail + ' ' + str(clip['start']) + ' ' + str(clip['end']))

	return ret

def shake_style(seq, **kwargs):
	""" Shake style output """
	def at_padding(n):
		""" create string of n 'ats' (@) """
		return '@' * n

	ret = []
	for clip in seq.clips:
		symbol = '#' if clip['padding'] == 4 else at_padding(clip['padding'])
		if clip['increment'] == 1:
			ret.append(seq.head + str(clip['start']) + '-' + str(clip['end']) + symbol + seq.tail)
		else: # incerement other than one get x-2, x3 etc.. postfix
			ret.append(seq.head + str(clip['start']) + '-' + str(clip['end']) + 'x' + str(clip['increment']) + symbol + seq.tail)

	return ret

def fl_style(seq, **kwargs):
	""" Filmlight baselight utils style output """
	ret = []
	for clip in seq.clips:
		ret.append(seq.head + "%." + str(clip['padding']) + 'F' + seq.tail + ':' + str(clip['start']) + '-' + str(clip['end']))

	return ret

def subst_strings(format_string, fps, tc_start, seq_name, clip_name, head, tail, start, end, padding, increment, seq_len, clip_len, index):
	""" create wildcard -> variable pairs, which can be used to regex the wild cards out of format string 
		This has been made a separate function, because it is shared between format_seq and format_str
		I am not happy about the messy way this substitution is formatted, but I have no better idea of keeping it tidy """
	# List of wild cards to substitute with variables
	subst = [('%F', seq_name),
			 ('%f', clip_name),
			 ('%h', head),
			 ('%t', tail),
			 ('%s', start),
			 ('%e', end),
			 ('%S', str(start).zfill(padding)),
			 ('%E', str(end).zfill(padding)),
			 ('%p', padding),
			 ('%i', increment),
			 ('%L', seq_len),
			 ('%l', clip_len),
			 ('%n', index),
			 ('%#', '#' * padding),
			 ('%@', '@' * padding)]

	# Timecode outputting wild cards are special as we need frame rate to be set
	if fps:
		subst += [('%<', get_timecode(start, fps, tc_start)),
				  ('%>', get_timecode((end + 1), fps, tc_start)), # Note TC had different ending style (+1) than frameseq
					  ('%-', get_timecode(seq_len, fps)), 	# Length should never be offset with tc_start
				  ('%=', get_timecode(clip_len, fps))]
	else:
		for wildcard in ['%<', '%>', '%-', '%=']:
			if format_string.find(wildcard) != -1:
				raise ValueError ("Timecode framerate must be set when using %< %> %- %-")

	return subst

def substitute_wildcards(format_string, subst_rules):
	ret_string = format_string

	# Loop for substituting each wildcard from list of wildcard -> subststring pairs
	for rule in subst_rules:
		ret_string = re.sub(rule[0], str(rule[1]), ret_string)
	return ret_string


def format_seq(seq, format_string, fps, tc_start, index):
	""" takes in seq and formats it based on format string """

	ret = []

	seq_len = seq.frame_amount()
	head = seq.head
	tail = seq.tail
	seq_name = str(seq)


	for clip in seq.clips:

		start = clip['start']
		end = clip['end']
		padding = clip['padding']
		increment = clip['increment']
		clip_name = Filesequence(head, [clip], tail).export()
		clip_len = Filesequence.get_clip_len(seq, clip) # running helper function from inside object passing objects data to it!

		subst = subst_strings(format_string, fps, tc_start, seq_name, clip_name, head, tail, start, end, padding, increment, seq_len, clip_len, index)


		ret_string = substitute_wildcards(format_string, subst)

		# If custom format returns similar results for many clips in a sequence output only one
		# This can happen if format is for example print total length of sequence "%L"
		try:
			if ret[-1] != ret_string:
				ret.append(ret_string)
		except IndexError:
			ret.append(ret_string)

	return ret

def format_str(s, format_string, fps, tc_start, index):
	""" input is string, so we can skip most of the wildcards, subst creation is passed with lots of hardcoded values (length of 1 etc.) """
	subst = subst_strings(format_string, fps, tc_start, s, s, s, "", 0, 0, 0, 0, 1, 1, index) 
	ret_string = substitute_wildcards(format_string, subst)

	return [ret_string]

def format_style(seq, **kwargs):
	""" unix 'stat' like wildcard output """
	format_string = kwargs['optional']
	fps = kwargs['fps']
	tc_start = kwargs['tc_start']
	index = kwargs['index']

	if type(seq) != str:
		ret = format_seq(seq, format_string, fps, tc_start, index)
	else:
		ret = format_str(seq, format_string, fps, tc_start, index)

	return ret

def rv_style(seq, **kwargs):
	""" RV style output, used by fsrv as well """

	def publish(seq, s, p):
		s = s[:-1]
		padding = '#' if p==4 else p * '@'
		return (seq.head + s + str(padding) + seq.tail)

	ret = []
	prev_padding = seq.clips[0]['padding']

	clip_str = ""

	for clip in seq.clips:
		if clip['padding'] == prev_padding:
			if clip['increment'] != 1:
				inc = 'x' + str(abs(clip['increment']))
			else:
				inc = ""
		
		else:

			ret.append(publish(seq, clip_str, prev_padding))
			prev_padding = clip['padding']
			clip_str = ""

		low = min(clip['start'], clip['end'])
		high = max(clip['start'], clip['end'])
		if low != high:
			clip_str += str(low) + '-' + str(high) + inc + ','
		else:
			clip_str += str(low) + ','

	ret.append(publish(seq, clip_str, prev_padding))
	
	return ret
