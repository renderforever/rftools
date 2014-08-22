""" 
Launch RV based on sequencelist
"""

from fsoutformat import rv_style
import subprocess
import collections
import os

def flatten(l):
    for el in l:
        if isinstance(el, collections.Iterable) and not isinstance(el, basestring):
            for sub in flatten(el):
                yield sub
        else:
            yield el

def fsrv(original_seqlist, modified_seqlist, **kwargs):

	rv_flags = kwargs['rv_flags']

	if os.environ.has_key('RV_EXECUTABLE_PATH'):
		rv_exec = os.environ['RV_EXECUTABLE_PATH']
	else:
		rv_exec = "rv"

	# Take entry from original seqlist if it exist, fall back to modified if original is None
	seqlist = map(lambda x: x[0] if x[0] else x[1], zip(original_seqlist, modified_seqlist))

	rv_seqlist = list(flatten(map(rv_style, seqlist)))

	if rv_seqlist:
		if rv_flags != "--":
			subprocess.check_call([rv_exec] + [rv_flags] + rv_seqlist)
		else:
			subprocess.check_call([rv_exec] + rv_seqlist)