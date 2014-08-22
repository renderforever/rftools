"""
all cli output is run through this 
"""

import sys

def print_cli(msg, quiet=False):
	if not quiet:
		sys.stderr.write(msg)