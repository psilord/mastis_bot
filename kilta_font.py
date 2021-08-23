# Code to perform Pango-like font cairo interactions and font 
# layout with the Kílta Font.

import os
import font_helper as fh
import kilta_utils as ku
from fontTools import ttLib
import math

# debugging
import python_object_stuff as pos
import cairo

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
		
		# Store units per Em (ensure to use a float!)
		self.units_per_em = float(self.tt['head'].unitsPerEm)

		# map from character ordinal to glyph name
		self.cmap = self.tt.getBestCmap()

		# map from tuple left/right glyph names to x kerning offset.
		self.kern_table = self.tt['kern'].getkern(0).kernTable

		# map from glyph_name to glyph_index in font
		self.gmap = self.tt.getReverseGlyphMap()

		# knowledge about each glyph's widths, key is glyph name, value
		# is an object which has a 'width' attribute in ems for the glpyh
		self.glyph_set = dict(self.tt.getGlyphSet())

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
	
	# Convert a mastis character to a glyph name 
	def get_glyph_name(self, mchar):
		mord = ord(mchar)
		mglyph_name = self.cmap.get(mord)
		return mglyph_name

	# Convert a mastis character to a glyph index (suitable for cairo)
	def get_glyph_index(self, mchar):
		mord = ord(mchar)
		mglyph_name = self.cmap.get(mord)
		return self.gmap.get(mglyph_name)
	
	# TODO: It is so hard to get correct glyph extent data from ttLib. WTF.
	def get_glyph_width(self, glyph_name):
		g = self.glyph_set.get(glyph_name)
		return g.width

	def get_glyph_lsb(self, glyph_name):
		g = self.glyph_set.get(glyph_name)
		return g.lsb
		
	# Given a single line of mastis characters, lay it out in accordance with
	# kerning rules against an origin of (0,0) using the size of the characters
	# in the font itself. We work from the raw ems units themselves and compute
	# what we need from first principles. According to manuals, the default dpi
	# of cairo's text rendering _appears_ to be 72dpi by inspection.
	def layout_line(self, ctx, mastis, font_size, dpi=72):
		# First, cut the mastis line into kerning pairs in the order of the
		# utterance.
		kpairs = []
		for i in range(len(mastis)):
			if (i+1 < len(mastis)):
				kpairs.append((mastis[i], mastis[i+1]))
			else:
				kpairs.append((mastis[i], None))
		#print(f"kpairs = {kpairs}")

		# Walk down the pairs converting to a list of:
		# [glyph_id, x_px, y_px] lists that indicate where to place 
		# the glyph relative to the location of the current pen.
		glayout = []
		dx_ems = 0
		dy_ems = 0
		dpi_scale = dpi / 72.0 # NOTE: Validate this equation
		font_scale = font_size * dpi_scale
		x_pen, y_pen = ctx.get_current_point()
		for pair in kpairs:
			if (pair[1] is not None):
				kern_val_ems = self.get_kerning_for_pair(pair[0], pair[1])
			else:
				kern_val_ems = 0

			kern_val_ems = 0

			current_glyph_index = self.get_glyph_index(pair[0])
			current_glyph_name = self.get_glyph_name(pair[0])
			current_glyph_width_ems = self.get_glyph_width(current_glyph_name)

			#print(f"cglyph[{pair[0]}] width: {current_glyph_width_ems}, kerning: {pair[0]}:{pair[1]}/{kern_val_ems}, dx_ems: {dx_ems}, dy_ems: {dy_ems}, kvems: {kern_val_ems}")

			# convert from em space to pixel space relative to the pen location.
			# Note: specifically written this way to minimize floating error.
			x_px = (dx_ems * font_scale) / self.units_per_em
			y_px = (dy_ems * font_scale) / self.units_per_em
			#print(f" '{pair[0]}': x_px: {x_px} y_px: {y_px}")
			glyph = cairo.Glyph(current_glyph_index, x_pen + x_px, y_pen + y_px)
			#print(f" glyph: {glyph}")
			glayout.append(glyph)

			# Now, figure out the advance and subtract the kerning for the
			# placement of the next glyph in em space. NOTE: that kerning
			# values are positive or negative as appropriate, so we simply
			# add it all together.
			dx_ems += current_glyph_width_ems + kern_val_ems
			# We don't handle vertical scripts, so ignore dy_ems.
			dy_ems = 0

		# TODO: Need to also return extents of line (which include the kerning)
		# as another value, that will make all kinds of other things easier.
		# Like computing the proper image width, etc, etc.
		return glayout

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

	# ######################
	# Dump out glyph name to glyph ID.
	# ######################
	glyph_map = tt.getReverseGlyphMap()
	print(f"Glyph Reverse Map: {glyph_map}")

	glyph_set = dict(tt.getGlyphSet())
	#print(f"Glyph Set: {glyph_set}")
	for glyf in glyph_set.keys():
		width = glyph_set.get(glyf).width
		lsb = glyph_set.get(glyf).lsb
		# Height can often be None.
		height = glyph_set.get(glyf).height
		#pos.introspect("glyph: ", glyph_set.get(glyf))
		print(f"glyf (in set): {glyf} -> lsb: {lsb}, width: {width}, height: {height}")
	
	# ######################
	# Dump out glyph order in font file
	# ######################
	glyph_order = tt.getGlyphOrder()
	print(f"glyph_order:")
	for idx in range(len(glyph_order)):
		print(f"  {glyph_order[idx]} @ loc {idx}")

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

# More debugging.
# A standalone function to test the kerning and visualize it under to 
# unkerned text. Top line is unkerned, bottom line is kerned.
def kern_test():
	WIDTH = 475
	HEIGHT = 128
	FONT_SIZE = 30
	kilta_text = "Këkketë rin in tuirachún nútokolsa li"
	kilta_text = "rin rin rin"
	kilta_text = "rin rin rin rin rin rin rin rin rin"
	
	kt = ku.KiltaTokenizer()
	mastis_text = kt.romanized_to_mastis(kilta_text.strip())

	kf = KiltaFont("./KiThree.ttf")
	face = kf.get_cairo_font_face()

	surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, WIDTH, HEIGHT)
	ctx = cairo.Context(surface)
	ctx.set_font_face(face)
	ctx.set_font_size(FONT_SIZE)
	# font_extents is (ascent, descent, height, max_x_advance, max_y_advance)
	font_extents = ctx.font_extents()

	# fill background with white
	ctx.rectangle(0, 0, WIDTH, HEIGHT)
	ctx.set_source_rgba(1.0, 1.0, 1.0, 1.0) # white
	ctx.fill()

	# Draw unkerned text
	ctx.set_source_rgba(0.0, 0.0, 0.0, 1.0) # black
	ctx.move_to(0, HEIGHT / 2.0 - FONT_SIZE - font_extents[1]) # descender
	ctx.show_text(mastis_text)
	line_extent = ctx.text_extents(mastis_text)
	print(f"Unkerned Glyph extents: {line_extent}")

	# Draw kerned text
	ctx.move_to(0, HEIGHT / 2.0)
	mastis_glyphs = kf.layout_line(ctx, mastis_text, FONT_SIZE)
	ctx.show_glyphs(mastis_glyphs)
	line_extent = ctx.glyph_extents(mastis_glyphs)
	print(f"Kerned Glyph extents: {line_extent}")

	# DEBUGGING
	ctx.move_to(WIDTH / 2.0, HEIGHT / 2.0)
	debug_text = kt.romanized_to_mastis("k")
	debug_mastis = kf.get_glyph_index(debug_text[0])
	debug_glyph = [cairo.Glyph(debug_mastis, WIDTH / 2.0, HEIGHT / 2.0 + 40)]
	ctx.show_glyphs(debug_glyph)
	ext = ctx.glyph_extents(debug_glyph)
	print(f"ext of mastis 'k' is {ext}")

	# Cleanup
	del ctx
	surface.write_to_png("hello.png")
	del surface
	print("Wrote image to hello.png")

def main():
	# The state of this function is forever in some debugging state.

	debugging()
	kern_test()
	return

	#kf = KiltaFont("./KiThree.ttf")
	#print(f"Cairo Font Face Object: {kf.get_cairo_font_face()}")
	#print(f"Kerning between'k' and 'i': {kf.get_kerning_for_pair('k', 'i')}")

if __name__ == '__main__':
	main()




