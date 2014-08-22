"""
Different functions that take in string and try to output filesequence object
"""

from Filesequence import Filesequence
import re

def split_tail(s, splitter):
	""" if tail is followed by digits separated by space let's assume those are our start and end point """
	splitted_tail = s.split(splitter)
	if len(splitted_tail) == 1: return s, 0, 0 # Nothing here, early termination
	if len(splitted_tail) == 3:
		try:
			start = int(splitted_tail[1])
			end = int(splitted_tail[2])
		except:
			start = 0
			end = 0
	if len(splitted_tail) == 2:
		# There is only one word following the tail. It could be "123-234" or "123:234"
		# extract digits from this string and try to force them to start and end
		digits = re.findall('\d+', splitted_tail[1])
		try:
			start = int(digits[0])
			end = int(digits[1])
		except:
			start = 0
			end = 0
	return splitted_tail[0], start, end

def printf_style(s, unused=None):
	""" fuzzy printf recognition, get's a bit messy. Basic idea is to split string to smaller clips
		Maybe we should use inbuilt .format()
		longname_example_clip.%04d.dpx 100 1000 
		----------[0]---------|----[1]--------- first_split 
		......................|[0|-[1]--------- second_split 
		......................|..|-[0]|[1]|[2]- tail_split """

	first_split = s.rsplit("%", 1)
	if len(first_split) == 1: return None # no '%' early termination
	second_split = first_split[1].split("d", 1)

	head = first_split[0]
	tail, start, end = split_tail(second_split[1], " ")
	try:
		padding = int(second_split[0])
	except:
		padding = 1 # Default to 1 padding

	new_clip = [{'start': start, 'end': end, 'padding': padding, 'increment': 1}]
	return Filesequence(head, new_clip, tail)

def filmlight_style(s, unused=None):
	""" assume input string is created by filmlight tools
		Format is head.%.3F.tail:0-10 

		starting with printf_style code and modify until ok """

	first_split = s.rsplit("%.", 1)
	if len(first_split) == 1: return None # does not look like FL early termination
	second_split = first_split[1].split("F", 1)
	if len(second_split) == 1: return None # does not look like FL still early termination

	head = first_split[0]
	tail, start, end = split_tail(second_split[1], ":")
	try:
		padding = int(second_split[0])
	except:
		padding = 0

	new_clip = [{'start': start, 'end': end, 'padding': padding, 'increment': 1}]
	return Filesequence(head, new_clip, tail)

def format_style(s, format):
	""" user provided format template """
	
	# NOT IMPLEMENTED
	pass
