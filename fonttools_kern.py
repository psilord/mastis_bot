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

	glyph_names = tt.getGlyphNames()
	print(f"Glyph Names: {glyph_names}")

	glyph_ids = list(map(lambda x : tt.getGlyphID(x), glyph_names))
	print(f"Glyph IDs: {glyph_ids}")

	glyph_set = tt.getGlyphSet()
	print(f"Glyph Set: {dict(glyph_set).keys()}")
	g = glyph_set['g']
	print(f"Glyph g: {g}")

	# ######################
	# Get character code to glyph name map
	# ######################
	cmap = tt['cmap']
	introspect("cmap", cmap)
	#print(f"cmap: {cmap.getcmap()}")

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

