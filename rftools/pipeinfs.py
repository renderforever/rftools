"""
Pipe in filesequence. Reads strings sent in through unixpipe and as commandline arguments. Checks which format strings are and
returns two lists modified and original. The actual conversion is done by Filesequence object at the time of object construction.

supported input formats for filesequence strings are:
'filesequence.[0-100x2@].dpx'
and so called mapped definition
'old_filesequence.[0-100x2@].dpx -> new_filesequence.[100-150@].dpx'
"""

import sys
import os
from time import sleep
from Filesequence import Filesequence

def stringtofs(s):
	""" takes in string and tries to return Filesequence object, most of the heavylifting is done by the object itself. Input might be messy so 
		we have fallback to returning pure strings (single files not part of filesequence)
		This wrapper is needed because we support two string definitions. a simple string and mapped string in format seq1 -> seq2 """

	splitted_s = s.split(' -> ')
	if len(splitted_s) > 1:
		
		try:
			original = Filesequence.from_string(splitted_s[0])
		except ValueError:
			original = splitted_s[0]
		try:
			modified = Filesequence.from_string(splitted_s[1])
		except ValueError:
			modified = splitted_s[1]	
		return original, modified
	else:
		try:
			return None, Filesequence.from_string(s)
		except:
			return None, s

def read_stdin():
	""" reads from pipe and creates a list """
	if not sys.stdin.isatty():
		return map(lambda s: s.rstrip(), sys.stdin.readlines())
	else:
		return []

def convert_fs(strings):
	original = []
	modified = []

	if len(strings) > 0:
		for s in strings:
			original_seq, modified_seq = stringtofs(s)
			original.append(original_seq)
			modified.append(modified_seq)

	return original, modified

def get_fs(args):
	""" read both pipe in and commandline args and return filesequence lists """

	pipedin = read_stdin()
	original, modified = convert_fs(pipedin + args)

	return original, modified