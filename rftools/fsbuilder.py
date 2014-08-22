"""
Takes in two filesequencelists (orig, modified) and does one of the following actions to them
cp, mv, ln
"""

import os
import sys
import shutil
from list_files import list_files
from Filesequence import Filesequence
from logger import print_cli

def get_dir_file(directory, filename):
	""" Join dir and filename. Simple os.path.join """
	if directory:
		combined = os.path.abspath(os.path.join(directory, filename))
		return combined
	else:
		return os.path.abspath(filename)

def inspect_landing_area(f):
	""" See beforehand if we are about to override a file, or are missing a directory """
	missing_path = None
	file_conflict = None

	path = os.path.dirname(f)
	if not os.path.exists(path):
		missing_path = path
	else:
		if os.path.exists(f):
			file_conflict = f

	return file_conflict, missing_path

def inspect_source(f):
	""" see that f exists """
	if not os.path.exists(f):
		return f
	else:
		return None

def reorder_ops(ops_list, conflicting_files):
	""" If there are files that already exist it might be that we can still go through the build we are about to move files. 
		Common example is if we offset filesequence by small amount. This creates situations where file might move over file further 
		down in sequence. If we reorder the move operations, we might clear the way so that none of the moves face conflicts. 

		this is a bit complicated:

		The algorithm works so that we have 'search' dictionary, that works as lookup table for conflicting filenames. 
		If file knows that it would move over something, it will stash itself into this 'search' dict for now.
		File that has no conflicts is added straight to the processing list as we are sure it cant step over anything. 
		After any add we always check is there somebody waiting on the list for this operation to happen and process it next.

		If adding file to return list would free up some conflict, but the conflicting entry has not been yet handled, we clear
		the conflict"""

	def ret_append(pair, search):
		""" append pair and check if we need to launch more appends """

		# Append the list with the pair
		ret = [pair]
		process_next = None
		freed_filename = pair[0]

		try:
			if search[freed_filename]:
				# freed_filename found in stash
				# put it to queue to be processed next empty added entry from stash
				process_next = search[freed_filename]
				del search[freed_filename]
			else:
				# Somebody is waiting for this insert, but it has not been handled yet, so when it's up it's ok to just add it
				# modifying search inside function nasty!
				del search[freed_filename]
		except:
			pass

		return ret, process_next

	search = {}
	ret_list = []
	ret_conflict = []

	# Init search dictionary, for all the filenames we know are in conflict
	for f in conflicting_files:
		search[f] = None

	for pair in ops_list:
		try:
			if not search[pair[1]]:
				# Search dict has this entry, but it's empty. Stash away this pair
				search[pair[1]] = pair

		except:
			# pair[1] doesn't step on anything so we can just add it to list
			process_next = pair
			# Check after appending this pair to list that if some other pair can be now added.
			# recursive approaches broke down with too long sequences
			while process_next:
				appended, process_next = ret_append(process_next, search)
				ret_list += appended


	# Flush any remaining conflicting files back to list
	for k, pair in search.iteritems():
		ret_list.append(pair)
		ret_conflict.append(pair[1]) 

	# We should have exactly the same amount of operations after this complicated delayed inserting
	assert (len(ret_list) == len(ops_list))

	return ret_list, ret_conflict

def get_ops(orig_seq, modified_seq, in_dir, out_dir):
	""" turn to and from sequence objects in to list of filename level operations """
	ops_list = []
	for pair in zip(list_files(orig_seq), list_files(modified_seq)): # list filesequences out as original modified -> file pairs
		ops_list.append((get_dir_file(in_dir, pair[0]), get_dir_file(out_dir, pair[1])))
	active_ops = filter(lambda pair: pair[0] != pair[1], ops_list) # Filter out those filepairs where to/from are identical
	return active_ops

def mkdir(dirlist, execute, quiet):
	for dir in dirlist:
		if execute:
		 	os.makedirs(dir)

		else:
		 	print_cli("dry-run: mkdir -p " + dir + "\n", quiet)

def report(error, perline, filelist, quiet):
	""" print whole bunch of lines with custom message, checking quiet in here bit odd """
	if not quiet:
		print_cli(error + '\n')
		for filename in filelist:
			print_cli("  " + perline + filename + '\n')

def check_conflicts(ops_list):
	""" Go through list of operations beforehand and return multiple lists that point to possible problems """
	missing_source_files = []
	missing_paths = []
	conflicting_files = []
	pruned_ops_list = []

	for pair in ops_list:
		missing_source = inspect_source(pair[0])
		conflict, path = inspect_landing_area(pair[1])
		
		if missing_source:
			missing_source_files.append(missing_source)
		else:
			pruned_ops_list.append(pair)

		if path:
			missing_paths.append(path)

		if conflict:
			conflicting_files.append(conflict)

	return pruned_ops_list, missing_paths, missing_source_files, conflicting_files

def builder(operation, original_seqlist, modified_seqlist, in_dir, out_dir, create_dirs=False, force=False, skip=False, quiet=False, execute=False):
	""" construct the to and from filelists, check for conflicts, prepare directories and do the move/link/copy etc... """
	
	ops_list = []

	for pair in zip (original_seqlist, modified_seqlist):
		original = pair[0] if pair[0] else pair[1]
		modified = pair[1]
		ops_list += get_ops(original, modified, in_dir, out_dir)

	ops_list, missing_paths, missing_source_files, conflicting_files = check_conflicts(ops_list)

	if missing_source_files:
		report("Warning, missing following source files:", "missing: ", missing_source_files, quiet)
		if not skip:
			raise OSError("missing files")

	if conflicting_files:
		if operation == mv: ops_list, conflicting_files = reorder_ops(ops_list, conflicting_files)
		if conflicting_files:
			report("Warning, following files already exist", "file exists: ", conflicting_files, quiet)
			if not force:
				raise OSError("files exist")

	if missing_paths:
		missing_paths = sorted(set(missing_paths)) # remove duplicate mentions of the same paths

		if not create_dirs:
			report("Warning, following paths should be created", "missing path: ", missing_paths, quiet)
			raise OSError("target paths missing")
		else:
			mkdir(missing_paths, execute, quiet)

	operation(ops_list, execute, force, quiet) # rfbuild passes in variable pointing to the actual function.
	if ops_list:
		if not execute:
			print_cli("run with --execute to actually run these operations\n", quiet)
	else:
		print_cli("nothing to do\n", quiet)

def check_writable(ops_list):
	""" go through all the landings one more time and check that they are writable """
	for pair in ops_list:
		if os.path.exists(pair[1]):
			if not os.access(pair[1], os.W_OK):		
				raise IOError ("build cancelled - [Errno 13] Permission denied: '" + pair[1] + "'")

def ln(ops_list, execute, force, quiet):

	check_writable(ops_list)

	for pair in ops_list:
		if execute:
			try:
				os.symlink(pair[0], pair[1])
			except OSError:
				if force:
					os.remove(pair[1])
					os.symlink(pair[0], pair[1])
		else:
			print_cli("dry-run: ln -s " + pair[0] + " " + pair[1] + "\n", quiet)


def mv(ops_list, execute, force, quiet):

	check_writable(ops_list)

	for pair in ops_list:
		if execute:
			shutil.move(pair[0], pair[1])
		else:
			print_cli("dry-run: mv " + pair[0] + " " + pair[1] + "\n", quiet)

def cp(ops_list, execute, force, quiet):

	check_writable(ops_list)

	for pair in ops_list:
		if execute:
			shutil.copyfile(pair[0], pair[1])
		else:
			print_cli("dry-run: cp" + pair[0] + " " + pair[1] + "\n", quiet)
