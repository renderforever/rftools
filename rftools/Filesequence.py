"""
Filesequence class definition
Each sequence contains fixed head and tail strings and one or more 'clips' of sequence numbering 
(so if frame 50 is missing from 100 frames there would be clips 0-49, 51-99)
Each clip contains increment number (stepping) and information on padding
1-9 increment 2 means 1 3 5 7 9. If number can't fit the provided padding it's ok to go over

General idea for now is that the object are more or less data storages. They only process data when constructing the object
or providing different views on it. Besides this I also access the internals straight without accessor functions, not sure if this pythonic or not.
"""

class Filesequence:
	""" Filesequence """

	head = ""
	clips = [{}] # List of clips in sequence. keywords start, end, padding, increment
	tail = ""

	def __init__(self, head, clips, tail):
		self.head = head
		self.clips = clips
		self.tail = tail
	
	@classmethod # Alternative constructor that takes in standard string format definiton of sequence
	def from_string(cls, s):
		

		def error_check(s):
			""" Look for common problems in filesequence strings """
			if s.count('[') != 1: return True
			if s.count(']') != 1: return True
			return False

		def error_check_clip(c):
			if c.count('@') == 0: return True
			if c.count('x') > 1: return True
			char_table = "-x@0123456789"
			if c.translate(None, char_table): return True
			return False

		def get_tail(s):
			""" tail is everything after last ] """
			i = s.rfind(']')
			return s[(i+1):]

		def get_head(s):
			""" head is everything before first [ """
			i = s.find('[')
			return s[:i]

		def get_clips(s):
			""" clip section is between first [] in sequence """		
			start = s.find('[')
			end = s.rfind(']')
			return s[start+1:end]

		def get_start(c):
			i = c[1:].find('-') + 1 # Skip first letter
			return int(c[:i])

		def get_end(c):
			first = c[1:].find('-') + 1 # if first letter because it might be negative framenumber
			last = c.find('x')
			if last == -1: last = c.find('@')
			return int(c[first+1:last])

		def get_padding(c):
			return c.count('@')

		def get_inc(c):
			first = c.find('x')
			if first != -1:
				last = c.find('@')
				return int(c[first+1:last])
			else:
				return 1

		def handle_clips(clip_section):
			clips = clip_section.split(',')
			ret_clips = []
			for clip in clips:
				if error_check_clip(clip): raise ValueError("Filesequence [clip] " + clip_section + " not properly formatted")
				start = get_start(clip)
				end = get_end(clip)
				padding = get_padding(clip)
				increment = get_inc(clip)

				ret_clips.append({'start': start, 'end': end,'padding': padding,'increment': increment})

			return ret_clips

		if error_check(s):
			raise ValueError ("string " + s + " not filesequence")

		head = get_head(s)
		tail = get_tail(s)

		clip_section = get_clips(s)
		clip_list = handle_clips(clip_section)

		return cls(head, clip_list, tail)

	def get_clip_len(self, clip):
		""" single clip of filesequence can increase or decrease by n steps, which makes calculating it's frame amount difficult 
			This is shared between frame_amount and unpack_frame.n_in_clip """
		return (max(clip['start'], clip['end']) - min(clip['start'], clip['end'])) / abs(clip['increment']) + 1


	def frame_amount(self):
		ret = 0 
		for clip in self.clips:
			ret += self.get_clip_len(clip)
		return ret

	def unpack_frame(self, n):
		""" give out filename of nth frame from filesequence object, supports running over the sequence end 
			n is not the frame number, but nth frame in the sequence
		"""

		def n_in_clip(clips, n):
			""" check if n is inside this clip """

			clip_length = self.get_clip_len(clips[0])
			if n >= (clip_length):
				try:
					return n_in_clip(clips[1:], n - clip_length)
		
				except IndexError: # last clip, roll over!
					return clips[0], n 
			else:
				return clips[0], n

		clip, nth = n_in_clip(self.clips, n)
		start = clip['start']
		inc = clip['increment']
		padding = clip['padding']
		frame = start + inc * nth
		
		return self.head + str(frame).zfill(padding) + self.tail

	def unpack(self):
		""" return list of all individual files in sequence """
		filelist = []

		for n in range(self.frame_amount()):
				filelist.append(self.unpack_frame(n))

		return filelist

	def export(self):
		""" The standard string format export from fst, defaulting to modified shake syntax
			Supports different padding between clips and easier to parse because clip section is isolated with []
		"""
		def formatted_clips(clips):
			ret = ""

			for clip in clips:
				if (clip['increment'] == 1):
					ret += str(clip['start']) + "-" + str(clip['end'])
				else:
					ret += str(clip['start']) + "-" + str(clip['end']) + "x" + str(clip['increment']) 

				ret += '@' * clip['padding']
				ret += ','

			ret = ret.rstrip(',')

			return ret

		return self.head + '[' + formatted_clips(self.clips) + ']' + self.tail

	def __repr__(self):
		return self.export()
