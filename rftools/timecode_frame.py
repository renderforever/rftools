""" 
Most frame inputs can also take timecode string. This is one centralized place to handle that conversion
"""

import os

def get_frame(input, base, zero_at=0):
	""" Get frame if it is not int try to read timecode string """
	
	def timecode_to_frame(tc, base, zero_at):
		if tc.find(':') == -1:
			raise ValueError("Timecode should be in format (xx:xx:)xx:xx")

		if tc[0] == "-": # Special case for negative tc
			negative = -1
			tc = tc[1:]
		else:
			negative = 1

		digits = map(int, tc.split(':'))
		limits = [None, 60, 60, base]
		if filter(lambda x: x, map(lambda x, y: x >= y, digits[1:], limits[1:])) or filter(lambda x: x, map(lambda x: x<0, digits)): 
			# Check that time code digits fit between 00-:00-59:00-59:00-(base-1)
			# Maybe too 'clever' and inefficent code
			raise ValueError("Timecode out of bounds " + tc)

		# If partial timecode is given extend it by adding entries to front
		while len(digits) < 4:
			digits = [0] + digits

		if zero_at:
			# zero_at offsets origo of our Timecode to Framenumber mapping
			# as this value might be given as timecode itself lets convert it through this same function
			offset = get_frame(zero_at, base)
		else:
			offset = 0

		multiplier = [60 * 60 * base, 60 * base, base, 1]

		# Multiply each cell with its 'multiplier factor' and count them together
		# Offset the resu
		return sum(map(lambda x, y: x*y , digits, multiplier)) * negative - offset

	try:
		return int(input)
	except:
		if not base:
			if os.environ.has_key('RF_FPS'):
				base = int(os.environ['RF_FPS'])
			else:
				raise ValueError("Timecode framerate must be set")
		return timecode_to_frame(input, base, zero_at)

def get_timecode(input, base, zero_at=0):
	""" turn int into timecode string """
	if not base:
		if os.environ.has_key('RF_FPS'):
			base = int(os.environ['RF_FPS'])
		else:
			raise ValueError("Timecode framerate must be set")
	
	frame = int(input)
	multiplier = [60 * 60 * base, 60 * base, base, 1]
	tc = []

	if zero_at:
		offset = get_frame(zero_at, base)
		frame -= offset

	if frame < 0: # Special case if our frame has been offset to negative
		frame = abs(frame)
		sign = '-'
	else:
		sign = ''

	# Scroll through our four fields and do the funky math
	# start by checking how many full hours fit in framenr, take those off, move to minutes etc...
	for mult in multiplier:
		tc_digit = (frame / mult)
		tc.append(tc_digit)
		frame -= mult * tc_digit

	return sign + str(tc[0]).zfill(2) + ':' + str(tc[1]).zfill(2) + ':' + str(tc[2]).zfill(2) + ':' + str(tc[3]).zfill(2)

def main():
	""" while debugging """

	print get_timecode(get_frame("00:24", 25, "-01:00:00:00"))

if __name__ == '__main__':
	main()