# fs_tests.py
#
# Don't know if this is how you do tests, but I will

import unittest

from rftools.fspacker import split_alphanum
from rftools.fspacker import fspacker
from rftools import fseditor
from rftools import fsbuilder
from rftools.Filesequence import Filesequence

def load_from_file(filename):
	fp = open(filename)
	return map(lambda s: s.rstrip(), fp.readlines())

class Alphanum_test(unittest.TestCase):
	test_values = [("lol.001.dpx", ["lol.", "001", ".dpx"]), 
	("", [""]),
	("a", ["a"]), 
	("what.212.dpx", ["what.", "212", ".dpx"]),
	("the.2000---", ["the.", "2000", "---"]),
	("s0", ["s", "0", ""]),
	("0s", ["", "0", "s"]),
	("string000string001string 002", ["string", "000", "string", "001", "string ", "002", ""]),
	("negative-100", ["negative", "-100", ""]),
	("alpha--100.num", ["alpha-", "-100", ".num"])]

	def test_alphanum_known_values(self):
		""" split_alphanum """
		for s, l in self.test_values:
			result = split_alphanum(s, True)
			self.assertEqual(l, result)

class Reorder_ops_test(unittest.TestCase):
	# Tests are lists of from->to tuples
	test_list = []
	test_conflict = []

	test_list.append([("0", "1"), ("1", "2"), ("2", "3")])
	test_conflict.append(["1", "2"])

	test_list.append([("0", "1"), ("1", "2"), ("2", "3"), ("different", "landing")])
	test_conflict.append(["1", "2", "landing"])

	test_list.append([("0", "1"), ("1", "2"), ("2", "0")])
	test_conflict.append(["0", "1", "2"])

	result_list = []
	result_conflict = []
	result_list.append([("2", "3"), ("1", "2"), ("0", "1")])
	result_conflict.append([])

	result_list.append([("2", "3"), ("1", "2"), ("0", "1"), ("different", "landing")])
	result_conflict.append(["landing"])

	result_list.append([("0", "1"), ("2", "0"), ("1", "2")])
	result_conflict.append(["1", "0", "2"])

	def test_reorders(self):
		for i in range(len(self.test_list)):
			a,b = fsbuilder.reorder_ops(self.test_list[i], self.test_conflict[i])
			for pair in a:
				self.test_list[i].remove(pair)

			self.assertEqual(self.test_list[i], [])
			self.assertEqual(a, self.result_list[i])
			self.assertEqual(b, self.result_conflict[i])

class Filesequence_test(unittest.TestCase):
	test_values_frame_amount = [("test[0-10@].dpx", 11),
	("test[0--10x-1@].dpx", 11),
	("test[0-20x2@@@].dpx", 11),
	("test[0-5@,5-25x5@@@,25--5x-1@@@@].d", 42)]

	test_values_unpack = [("seq[50-55@,100-80x-5@@@]", ["seq50", "seq51", "seq52", "seq53", "seq54", "seq55", "seq100", "seq095", "seq090", "seq085", "seq080"])]

	test_filenamelist = load_from_file("test_filelist.txt")

	def test_frame_amount(self):
		""" frame amount """
		for s, i in self.test_values_frame_amount:
			fs = Filesequence.from_string(s)
			length = fs.frame_amount()
			self.assertEqual(i, length)

	def test_unpack(self):
		""" unpack() """
		for s, l in self.test_values_unpack:
			fs = Filesequence.from_string(s)
			result = fs.unpack()
			self.assertEqual(l, result)

	def test_roundtrip(self):
		""" filelist to sequencestrings, and back """
		seqs = fspacker(self.test_filenamelist, False, True, True)
		ret_list = []
		for seq in seqs:
			ret_list += seq.unpack()

		self.assertEqual(self.test_filenamelist, ret_list)

if __name__ == "__main__":
    unittest.main()