# Code to perform Pango-like font cairo interactions and font 
# layout with the Kílta Font.

import os
import font_helper as fh
from fontTools import ttLib

class KiltaFont():
	def __init__(self, font_path):
		self.font_path = os.path.abspath(font_path)

		# Load and create a Cairo Font Face object that suitable for 
		# cairo's font processing.
		self.cairo_font_face = \
			fh.create_cairo_font_face_for_file(self.font_path, 0)

		# Create a _different_ font object with a different API 
		# suitable for kerning processing. It sucks we need to use two 
		# different APIs
		self.tt = ttLib.TTFont(self.font_path)
		# map from character ordinal to glyph name
		self.cmap = self.tt.getBestCmap()
		# map from tuple left/right glyph names to x kerning offset.
		self.kern_table = self.tt['kern'].getkern(0).kernTable
		# map from glyph_name to glyph_index in font
		self.gmap = self.tt.getReverseGlyphMap()

	def get_cairo_font_face(self):
		return self.cairo_font_face
	
	# NOTE: This function expects the mastis encoding.
	def get_kerning_for_pair(self, left_char, right_char):
		left_ord = ord(left_char)
		left_glyph_name = self.cmap.get(left_ord)
		if left_glyph_name is None:
			return 0

		right_ord = ord(right_char)
		right_glyph_name = self.cmap.get(right_ord)
		if right_glyph_name is None:
			return 0

		kern_val = self.kern_table.get((left_glyph_name, right_glyph_name))
		if kern_val is None:
			return 0

		return kern_val
	
	# Convert a mastis character to a glyph index (suitable for cairo)
	def get_glyph_index(self, mchar):
		mord = ord(mchar)
		mglyph_name = self.cmap.get(mord)
		return self.gmap.get(mglyph_name)
		
	# Given a single line of mastis characters, lay it out in accordance with
	# kerning rules against an origin of (0,0) using the size of the characters
	# in the font itself.
	def layout_line(self, mastis):
		# First, cut the mastis line into kerning pairs in the order of the
		# utterance.
		kpairs = []
		for i in range(len(mastis)):
			if (i+1 < len(mastis)):
				kpairs.append((mastis[i], mastis[i+1]))
			else:
				kpairs.append((mastis[i], None))

		# Then, assemble a [[char, kern_off], .....] list that is
		# in the order of the original mastis line.
		klets = \
			map(lambda kp : [k[0], self.get_kerning_for_pair(kp[0], kp[1])], \
				kpairs)

		# TODO: Keep going in transformations until I get to a list of
		# glyph indexes with x,y positions for where to put them.




# Useful standalone demonstration code for getting stuff out of ttLib.
def debugging():
	tt = ttLib.TTFont(os.path.abspath("./KiThree.ttf"))
	print("Loaded ./KiThree.ttf")

	print(f"Units Per Em: {tt['head'].unitsPerEm}")

	# ######################
	# Glyph chicanery
	# ######################

	glyph_names = tt.getGlyphNames()
	print(f"Glyph Names: {glyph_names}")

	glyph_ids = list(map(lambda x : tt.getGlyphID(x), glyph_names))
	print(f"Glyph IDs: {glyph_ids}")

	glyph_map = tt.getReverseGlyphMap()
	print(f"Glyph Reverse Map: {glyph_map}")

	glyph_set = dict(tt.getGlyphSet())
	print(f"Glyph Set: {glyph_set}")
	for glyf in glyph_set.keys():
		width = glyph_set.get(glyf).width
		# Height can often be None.
		height = glyph_set.get(glyf).height
		print(f"glyf: {glyf} -> width: {width}, height: {height}")

	# ######################
	# Get character code to glyph name map
	# ######################
	cmap = tt.getBestCmap()
	print(f"cmap: {cmap}")
	for char_ord_val in cmap.keys():
		# ord_val -> glyph_name
		print(f"cmap entry: {char_ord_val}('{chr(char_ord_val)}') -> {cmap[char_ord_val]}")

	# ######################
	# Figure out access to Kerning table
	# ######################
	kern = tt['kern']
	kern_table = kern.getkern(0).kernTable

	print(f"kern table kernTable: {kern_table}")
	for pair in kern_table.keys():
		left, right = pair
		kern_val = kern_table[pair]
		print(f"kerning: '{left}':'{right}' = {kern_val}")

def main():
	debugging()
	return

	#kf = KiltaFont("./KiThree.ttf")
	#print(f"Cairo Font Face Object: {kf.get_cairo_font_face()}")
	#print(f"Kerning between'k' and 'i': {kf.get_kerning_for_pair('k', 'i')}")

if __name__ == '__main__':
	main()




