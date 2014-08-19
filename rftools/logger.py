# logger.py
#
# All optional cli output messages and possibly output to file for debugging

import sys

def print_cli(msg, quiet=False):
	if not quiet:
		sys.stderr.write(msg)