"""
Tiniest helper script to do smart unpack, which takes into account that file being listed might be nonexistent, 
single file (string) or sequence representation (Filesequence)
"""

from Filesequence import Filesequence

def list_files(seq):
	if seq:
		try:
			return seq.unpack()
		except AttributeError:
			return [seq]
	else:
		return []