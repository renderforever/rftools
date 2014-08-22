""" Iterates over individual files in a sequence and runs custom command on each """

import os
import subprocess
from list_files import list_files
from rftools.logger import print_cli

def fscmd(original_seqlist, modified_seqlist, cmd, execute, quiet):
	
	args_proto = cmd[1].split(" ")

	for pair in zip(original_seqlist, modified_seqlist):
		originals = list_files(pair[0]) if pair[0] != None else list_files(pair[1])
		modifieds = list_files(pair[1])

		for entry in zip(originals, modifieds):
			args = map(lambda x: x.replace("%original", entry[0]), args_proto)
			args = map(lambda x: x.replace("%modified", entry[1]), args)

			if execute:
				subprocess.check_call([cmd[0]] + args)
			else:
				print_cli("dry-run: " + cmd[0] + " " + " ".join(args) + "\n", quiet)

	if not execute:
		print_cli("run with --execute to actually run these operations\n", quiet)