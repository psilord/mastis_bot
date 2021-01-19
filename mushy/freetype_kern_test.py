import freetype as ft
import itertools as it
import os

# debugging for when I get some object out of the freetype API that 
# isn't documented.
def get_methods(obj):
	object_methods = [method_name for method_name in dir(obj)
                  if callable(getattr(obj, method_name))]
	return object_methods

def get_attributes(obj):
	return dir(obj)


def main():
	# Initialize the face
	face = ft.Face(os.path.abspath("../KiThree.ttf"))
	print(f"Loaded KiThree.ttf...")

	# Get the defined char map
	char_list = [char for char in face.get_chars()]
	print(f" chars: {char_list}")

	# Find kerning between all glyphs. The all_pairs here really is all pairs
	# and not combinations.

	all_pairs = list(it.product(char_list, repeat=2))

	for pair in all_pairs:
		left, right = pair
		left_charcode, left_glyphindex = left
		right_charcode, right_glyphindex = right

		# validity check
		if left_glyphindex != face.get_char_index(left_charcode):
			print("Left Error")
			os.exit(1)
		if right_glyphindex != face.get_char_index(right_charcode):
			print("Right Error")
			os.exit(1)

		# Get the kerning information
		kern_ki = face.get_kerning(left_glyphindex,right_glyphindex, \
			ft.FT_KERNING_MODES["FT_KERNING_UNSCALED"])

		# TODO: Why is the vector always zero?
		# ANSWER: Because the kerning info is in GPOS and not in the
		# kern table for the font, and ftreetype cannot read it!
		print(f" kerning -> '{chr(left_charcode)}{chr(right_charcode)}' is " 
				f"{(kern_ki.x, kern_ki.y)}")

if __name__ == '__main__':
	main()

