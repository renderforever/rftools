"""
takes in list of files and returns sequences as Filesequence object where there is one 
"""

from Filesequence import Filesequence
from types import *
import string
import re
import fseditor
import sequence_math

def split_alphanum(s, allow_negative):
	""" split s in to list of words divided where digits turn non digits 
		Bit of trouble is seen for negative numbers if allowed so that - in front of digit is digit	"""

	if allow_negative:
		regex = '([0-9]+|-[0-9]+)'
	else:
		regex = regex = '([0-9]+)'

	ret = re.split(regex, s)

	return ret

def single_seq(s, negative=False):
	""" takes in single string and tries to force it to one frame seq.
		This means that sequence has at least some digits
		Taking the ugly way out and using Filesequence object from_string constructor to figure out sequence formatting """

	splitted = split_alphanum(s, negative)

	matched = None
	modified = []

	for item in splitted[::-1]: # note reversed list
		if not matched and re.match('.*\d+', item): # item contains digits and can start with -
			matched = 1
			item = '[' + item + '-' + item + (len(item) * '@') + ']'
		modified.append(item) 

	modified.reverse()

	try:
		return [Filesequence.from_string(''.join(modified))]
	except:
		return None

def detect_sequences(filelist, start=0, short=False, negative=False):
	""" iterate through the list as long as they conform to certain filesequence logic. 
		exit with info where we left off """


	def increment_of_n(filelist, negative=False):
		""" Determine if filenames in 'filelist' are part of same sequence (grow linearilly) and by how much """

		def numerify(start, end):
			""" try to extract numerical details of these two fields. """

			try:
				return {'start': int(start), 'end': int(end), 'padding': min(len(start),len(end))}
			except ValueError:
				return None


		def compare(a,b):
			""" take two filenames splitted to alphanum pairs and check that they have only one changing element 
				returns 'squashed' filename_proto which is three part list of [head, {dictionary describing changing field}, tail] """

			ret = []
			squash = ""
			for first, second in zip(a,b):
				if first == second:
					squash += first # identical fields between a and b are squashed to simple string
				else: # found changing element
					ret.append(squash)
					num = numerify(first, second) # create num dict which describes the properties of sequence numbering

					if num: 
						ret.append(num)
					else:
						return None # Ugly early terminate if either changing element is not int

					squash = ""

			ret.append(squash)

			if len(ret) != 3: # Three parter means that we have change in only one element and no more or less
				return None
			else:	
				return ret

		def get_increment(numbers):
			""" take in numbers dict and figure at what distance and direction the sequence is going """

			first = numbers['start']
			second = numbers['end']

			return second - first

		def filesequence_from_proto(squashed_filename, increment):
			""" We have all the components to create Filesequence object, this finishes the formatting """

			start = squashed_filename[1]['start']
			end = start + increment * 2
			padding = squashed_filename[1]['padding']

			return Filesequence(squashed_filename[0], 
								[{'start': start,
								'end': end,
								'padding': padding,
								'increment': increment}], 
									squashed_filename[2])

		splitted_list = map(split_alphanum, filelist, len(filelist) * [negative]) # Chop list to to strings and digits
		if len(splitted_list[0]) != len(splitted_list[1]): return None # early termination if the files contain different amount of num/alphanum pairs

		file_proto = compare(splitted_list[0],splitted_list[1])

		if file_proto: 
			increment = get_increment(file_proto[1])

			if increment:
				return filesequence_from_proto(file_proto, increment)
		
		return None

	def expand_fileseq(fileseq, n):
		""" So we have short filesequence, we want to expand it to length of n """
		start = fileseq.clips[0]['start']
		inc = fileseq.clips[0]['increment']
		padding = fileseq.clips[0]['padding']
		new_end = start + inc * n

		return Filesequence(fileseq.head, [{'start': start, 'end': new_end, 'padding': padding, 'increment': inc}], fileseq.tail)

	ret = []
	end = start # End tells Where we dropped of

	if (start+1) < len(filelist):
		start_of_seq = increment_of_n([filelist[start], filelist[start+1]], negative) # are these two files part of sequence, which sequence
	else:
		start_of_seq = None

	if start_of_seq: 
		# If we have start of sequence figured out, loop it forward. Non loopy way of doing this would be preferred
		# This count until hit, break loop thing feels shaky
		n = 1

		for i in range(start+1, len(filelist)):
			if filelist[i] != start_of_seq.unpack_frame(n):	# get nth element of our assumed sequence, and check it against real world filename
				# If it does not match, we give the sequence benefit of doubt and shrink it's padding by one and try again.
				# Otherwise sequence 100-0 would come back as [100@@@,99-10@@,9-0@], eventhough [100-0@] is legal
				start_of_seq.clips[0]['padding'] -= 1
				if filelist[i] != start_of_seq.unpack_frame(n):
					start_of_seq.clips[0]['padding'] += 1
					break
				else:
					n += 1
			else:
				n += 1

		ret.append(expand_fileseq(start_of_seq, n - 1))
		end = start + n

	else:

		if short:
			# There is no match, but if asked try to return one frame sequence
			ret = single_seq(filelist[start], negative)

		if not ret:
			ret = [filelist[start]] # Single file without numbers, return string (!)

		end = start + 1
		
	return ret, end

def fspacker(filelist, inv, short, negative):
	""" Launch sequence detection as long as necessary and merge results """

	def merge_filesequences(alist, blist):
		""" one or None item containing blist will be connected to the end of alist either as a subclip or sequence of it's own """
		if len(alist) == 0 : return blist
		if len(blist) == 0: return alist # early termination if blist is empty
		b = blist[0] 

		a = alist[-1]

		try:
			if (a.head == b.head) and (a.tail == b.tail):
				a.clips += b.clips
				return alist
			else:
				return alist + blist
		except AttributeError:
			return alist + blist

	seqlist = []
	n = 0

	while n < len(filelist):
		sequence, n = detect_sequences(filelist, n, short, negative)
		seqlist = merge_filesequences(seqlist, sequence)

	if inv:
		seqlist = map(sequence_math.invert, seqlist)
		seqlist = filter(lambda seq: seq != None, seqlist)

	return seqlist