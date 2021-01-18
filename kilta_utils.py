#!/usr/bin/python3

# This code handles the tokenization of Kílta text into tokens some of which
# represent letters or letter combinations and others represent grammatical
# constructs like the topical marker or attribute marker.

# references:
# https://docs.python.org/3.2/library/re.html#writing-a-tokenizer

import collections
import re
import random as rnd

KToken = collections.namedtuple('KToken', ['typ', 'value', 'line', 'column'])

class KiltaTokenizer:
	# The Key is a lexical TOKEN type, 
	# The Value is a list of encodings that represents it in the Mastis 
	# TTF file.
	mastis_encoding = {
		'TOPIC'			: ['/'],
		'ATTR'			: ['-'],

		'AU'			: ['a', 'u'],
		'AI_FIN'		: ['a', 'j'],
		'AI'			: ['a', 'i'],

		# Lexer produces UI_FIN, but sometimes we exchange it with UI_FIN_ALT
		# when converting the token stream to mastis.
		'UI_FIN'		: ['u', 'i'],
		'UI_FIN_ALT'	: ['u', 'j'],

		'UI'			: ['u', 'i'],

		'SHORT_I'		: ['i'],
		'LONG_I'		: ['í'],
		'SHORT_U'		: ['u'],
		'LONG_U'		: ['ú'],
		'SHORT_E'		: ['e'],
		'LONG_E'		: ['é'],
		'SHORT_O'		: ['o'],
		'LONG_O'		: ['ó'],
		'MID_E'			: ['ë'],
		'SHORT_A'		: ['a'],
		'LONG_A'		: ['á'],
		'PP'			: ['P'],
		'P'				: ['p'],
		'VV'			: [],		# TODO: No encoding!
		'V'				: ['v'],
		'MM'			: ['M'],
		'M'				: ['m'],
		'TT'			: ['T'],
		'T'				: ['t'],
		'SS'			: ['S'],
		'S'				: ['s'],
		'NN'			: ['N'],
		'N'				: ['n'],
		'RR'			: ['R'],
		'R'				: ['r'],
		'LL'			: ['L'],
		'L'				: ['l'],
		'CCH'			: [],		# TODO: No encoding!
		'CH'			: ['c'],
		'KK'			: ['K'],
		'K'				: ['k'],
		'HH'			: [],		# TODO: No encoding
		'H'				: ['h'],
		'KKW'			: [],		# TODO: No encoding
		'KW'			: ['q'],
		'HHW'			: [],		# TODO: No encoding
		'HW'			: ['x'],

		# TODO: These are not processed correctly yet.
		'TEN'			: ['['],
		'ONE'			: ['1'],
		'TWO'			: ['2'],
		'THREE'			: ['3'],
		'FOUR'			: ['4'],
		'FIVE'			: ['5'],
		'SIX'			: ['6'],
		'SEVEN'			: ['7'],
		'EIGHT'			: ['8'],
		'NINE'			: ['9'],

		'PERIOD'		: ['.'],
		'COMMA'			: ['.'],
		'EXCLAMATION'	: [],		# TODO: No encoding.
		'QUESTION'		: [],		# TODO: No encoding
		'COLON'			: [':'],
		'SEMI'			: [';'],

		'NEWLINE'		: ['\n'],
		'SPACE'			: [' '],
		'TAB'			: ['	'],
		'SECTION'		: ['$', '%', '$'],

		'UNK'			: [],		# TODO: No encoding

	}

	# A lexical analyzer to cut apart the Kílta into token that affect
	# Mastis rendering.
	def tokenize(self, s):
		token_specification = [
			# Special grammatical markers
			('TOPIC',		r'\b[Nn][Ëë]\b'),
			('ATTR',		r'\b[Vv][Ëë]\b'),

			# Dipthongs
			('AU',			r'[Aa][Uu]'),
			('AI_FIN',		r'[Aa][Ii]\b'),
			('AI',			r'[Aa][Ii]'),

			# Not dipthongs, but may Mastis affect rendering
			('UI_FIN',		r'[Uu][Ii]\b'),
			('UI',			r'[Uu][Ii]'),

			# Vowels
			('SHORT_I',		r'[Ii]'),
			('LONG_I',		r'[Íí]'),
			('SHORT_U',		r'[Uu]'),
			('LONG_U',		r'[Úú]'),
			('SHORT_E',		r'[Ee]'),
			('LONG_E',		r'[Éé]'),
			('SHORT_O',		r'[Oo]'),
			('LONG_O',		r'[Óó]'),
			('MID_E',		r'[Ëë]'),
			('SHORT_A',		r'[Aa]'),
			('LONG_A',		r'[Áá]'),

			# Consonants (in order to greedily process long versions first)
			('PP',			r'[Pp][Pp]'),
			('P',			r'[Pp]'),
			('VV',			r'[Vv][Vv]'),
			('V',			r'[Vv]'),
			('MM',			r'[Mm][Mm]'),
			('M',			r'[Mm]'),
			('TT',			r'[Tt][Tt]'),
			('T',			r'[Tt]'),
			('SS',			r'[Ss][Ss]'),
			('S',			r'[Ss]'),
			('NN',			r'[Nn][Nn]'),
			('N',			r'[Nn]'),
			('RR',			r'[Rr][Rr]'),
			('R',			r'[Rr]'),
			('LL',			r'[Ll][Ll]'),
			('L',			r'[Ll]'),
			('CCH',			r'[Cc][Cc][Hh]'),
			('CH',			r'[Cc][Hh]'),
			('KK',			r'[Kk][Kk]'),
			('K',			r'[Kk]'),
			('HH',			r'[Hh][Hh]'),
			('H',			r'[Hh]'),
			('KKW',			r'[Kk][Kk][Ww]'),
			('KW',			r'[Kk][Ww]'),
			('HHW',			r'[Hh][Hh][Ww]'),
			('HW',			r'[Hh][Ww]'),

			# Digits
			('TEN',			r'\b[1][0]\b'),
			('ONE', 		r'[1]'),
			('TWO', 		r'[2]'),
			('THREE', 		r'[3]'),
			('FOUR', 		r'[4]'),
			('FIVE', 		r'[5]'),
			('SIX', 		r'[6]'),
			('SEVEN', 		r'[7]'),
			('EIGHT', 		r'[8]'),
			('NINE', 		r'[9]'),

			# Punctuation
			('PERIOD', 		r'[.]'),
			('COMMA', 		r'[,]'),
			('EXCLAMATION',	r'[!]'),
			('QUESTION',	r'[?]'),
			('COLON',		r'[:]'),
			('SEMI',		r'[;]'),
			('SECTION',		r'[%]'), # TODO: Extension, ask wm about it.

			# We want to specifically keep track of whitespace and what kind.
			('NEWLINE',		r'[\n]'),
			('SPACE',		r'[ ]'),
			('TAB',			r'[\t]'),

			('UNK',			r'.'),		# anything else we don't know.
		]
		tok_regex = '|'.join('(?P<%s>%s)' % \
			pair for pair in token_specification)
		get_token = re.compile(tok_regex).match
		line = 1
		pos = line_start = 0
		mo = get_token(s)
		while mo is not None:
			typ = mo.lastgroup
			if typ == 'NEWLINE':
				line_start = pos
				line += 1
			val = mo.group(typ)

			yield KToken(typ, val, line, mo.start()-line_start)

			pos = mo.end()
			mo = get_token(s, pos)

		if pos != len(s):
			raise RuntimeError('Unexpected character %r on line %d' \
				%(s[pos], line))

	# A means to simply convert the tokenizer's iterable into an immediate list.
	def tokenize_all(self, s):
		return [token for token in self.tokenize(s)]
	
	def token_to_mastis(self, token_type):
		if token_type in self.mastis_encoding:
			return self.mastis_encoding[token_type]
		return []

	# Convert the utterance from the romanized version to the mastis encoding.
	def romanized_to_mastis(self, utterance):
		mastis_encodings = []
		for token in self.tokenize(utterance):
			typ = token.typ
			# Handle the (guessed) probabilities for UI_FIN
			if typ == 'UI_FIN':
				if rnd.random() <= .10:
					typ = 'UI_FIN_ALT'
			enc = self.token_to_mastis(typ)
			mastis_encodings.extend(enc);

		# join array into a string
		return "".join(mastis_encodings)

# --------------------------------------------------------------------------

def main():
	kilta_text = '''
		Këkketë rin in tuirachún nútokolsa li chanítirë. 
		Ívu ahëkará ermúlëstët, tuirachún ahëkará tin ochukár, 
		emmot li vonin chaso. 
		Luë rin në ahëkará mai tíchët om mai oto.
	'''

	kt = KiltaTokenizer()

	# Demonstrate the lazy version
	token_count = 0
	for token in kt.tokenize(kilta_text):
		token_count += 1
		val = "\\n" if token.value == "\n" else token.value
		val = "\\t" if val == "\t" else val 
		enc = kt.token_to_mastis(token.typ)
		print(f"{val:2} -> {token.typ:12} -> {enc}")
	print(f"Lazy version found {token_count} tokens.")
	
	print("The kilta text:")
	print(kilta_text)
	print("The mastis text:")
	print(kt.romanized_to_mastis(kilta_text))

	# demonstrate the eager list version
	ret = kt.tokenize_all(kilta_text)
	print(f"Eager version found {len(ret)} tokens.")

	if token_count != len(ret):
		print("ERROR! The lazy and eager versions differed!")

if __name__ == '__main__':
	main()
