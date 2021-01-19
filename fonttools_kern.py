# A program to test getting kerning  info out of a TTF

import os
from fontTools import ttLib

# debugging for when I get some object out of the freetype API that 
# isn't documented.
def get_methods(obj):
	object_methods = [method_name for method_name in dir(obj)
						if callable(getattr(obj, method_name))]
	return object_methods

def get_attributes(obj):
	return dir(obj)

def introspect(msg, obj):
	try:
		print(f"{msg} attributes: {get_attributes(obj)}")
	except:
		print(f"{msg} attributes: Not iterable. Sorry.")
		os.exit(1)

	try:
		print(f"{msg} methods: {get_methods(obj)}")
	except:
		print(f"{msg} methods: Not iterable. Sorry.")
		os.exit(1)


def main():
	tt = ttLib.TTFont(os.path.abspath("./KiThree.ttf"))
	print("Loaded ./KiThree.ttf")

	# ######################
	# Glyph chicanery
	# ######################

	glyph_names = tt.getGlyphNames()
	print(f"Glyph Names: {glyph_names}")

	glyph_ids = list(map(lambda x : tt.getGlyphID(x), glyph_names))
	print(f"Glyph IDs: {glyph_ids}")

	glyph_map = tt.getReverseGlyphMap()
	print(f"Glyph Reverse Map: {glyph_map}")

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

if __name__ == '__main__':
	main()

