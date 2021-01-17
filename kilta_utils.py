#!/usr/bin/python3

# This code handles the tokenization of Kílta text into tokens some of which
# represent letters or letter combinations and others represent grammatical
# constructs like the topical marker or attribute marker.

# references:
# https://docs.python.org/3.2/library/re.html#writing-a-tokenizer

import collections
import re

KToken = collections.namedtuple('KToken', ['typ', 'value', 'line', 'column'])

def kilta_tokenize(s):
	token_specification = [
		# Special grammatical markers
		('TOPIC',		r'\b[Nn][Ëë]\b'),
		('ATTR',		r'\b[Vv][Ëë]\b'),

		# Dipthongs
		('AU',			r'[Aa][Uu]'),
		('AI',			r'[Aa][Ii]'),

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
		('HKW',			r'[Hh][Hh][Ww]'),
		('HW',			r'[Hh][Ww]'),

		# Digits
		('TEN',			r'\w[1][0]\w'),
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

		# We want to specifically keep track of whitespace and what kind.
		('NEWLINE',		r'[\n]'),
		('SPACE',		r'[ ]'),
		('TAB',			r'[\t]'),

		('UNK',			r'.'),		# anything else we don't know.
	]
	tok_regex = '|'.join('(?P<%s>%s)' % pair for pair in token_specification)
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
		raise RuntimeError('Unexpected character %r on line %d' %(s[pos], line))

# A means to simply convert the tokenizer's iterable into an immediate list.
def kilta_tokenize_all(s):
	return [token for token in kilta_tokenize(s)]

def main():
	kilta_text = '''
		Këkketë rin in tuirachún nútokolsa li chanítirë. 
		Ívu ahëkará ermúlëstët, tuirachún ahëkará tin ochukár, 
		emmot li vonin chaso. 
		Luë rin në ahëkará mai tíchët om mai oto.
	'''

	for token in kilta_tokenize(kilta_text):
		val = "\\n" if token.value == "\n" else token.value
		val = "\\t" if val == "\t" else val 
		print(f"{val:2} -> {token.typ}")

	# demonstrate the list version
	#print(kilta_tokenize_all(kilta_text))

if __name__ == '__main__':
	main()
