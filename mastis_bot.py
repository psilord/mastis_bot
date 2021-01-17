# References:
# https://realpython.com/how-to-make-a-discord-bot-python/
# https://discordpy.readthedocs.io/en/latest/api.html
# https://zetcode.com/gfx/pycairo/
# https://pycairo.readthedocs.io/en/latest/reference/index.html
# https://heuristically.wordpress.com/2011/01/31/pycairo-hello-world/
# https://stackoverflow.com/questions/32321216/making-a-memory-only-fileobject-in-python-with-pyfilesystem
# https://docs.pyfilesystem.org/en/latest/interface.html
# https://pymotw.com/2/textwrap/
#
# Crappy instructions to install:
# sudo apt install python3-dotenv
# pip3 install -U discord.py
# pip3 install -U fs
# pip3 install -U pycairo
# python3 mastis-bot.py

import os
import re
import discord
import math
import cairo
import textwrap as tw
from dotenv import load_dotenv
from datetime import date
from fs.memoryfs import MemoryFS
import font_helper as fh
import kilta_utils as ku

load_dotenv()

# Found in the unchecked in .env file that must be in the cwd of the
# running script...
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_NAME = os.getenv("DISCORD_GUILD_NAME")
CHANNEL_NAME = os.getenv("DISCORD_CHANNEL_NAME")
MASTIS_FONT = os.path.abspath(os.getenv("MASTIS_FONT"))
MASTIS_FONT_FACE = fh.create_cairo_font_face_for_file(MASTIS_FONT, 0)


# Calculate Kílta cycle time
def do_aunka():
	EPOCH = date(2001, 9, 5)	# Sep 5, 2001 - cycle initiated
	today = date.today()
	days = today - EPOCH
	au = ['Kolkol', 'Immira', 'Nurës', 'Kokwara', 'Aunka'][days.days % 5]
	kiv = ['Rin', 'Ussala', 'Itar'][days.days % 3]
	tun = ['Lastun', 'Anlastun', 'Tillastun', 'Vallastun', 'Lólastun', 
		   'Nirusattun', 'Sattun'][today.timetuple().tm_wday]
	return "{} {} {}".format(au, kiv, tun)

def do_cairo():
	WIDTH, HEIGHT = 32, 32

	surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, WIDTH, HEIGHT)
	ctx = cairo.Context(surface)

	ctx.scale(WIDTH, HEIGHT)  # Normalizing the canvas

	pat = cairo.LinearGradient(0.0, 0.0, 0.0, 1.0)
	pat.add_color_stop_rgba(1, 0.7, 0, 0, 0.5)  # First stop, 50% opacity
	pat.add_color_stop_rgba(0, 0.9, 0.7, 0.2, 1)  # Last stop, 100% opacity

	ctx.rectangle(0, 0, 1, 1)  # Rectangle(x0, y0, x1, y1)
	ctx.set_source(pat)
	ctx.fill()

	ctx.translate(0.1, 0.1)  # Changing the current transformation matrix

	ctx.move_to(0, 0)
	# Arc(cx, cy, radius, start_angle, stop_angle)
	ctx.arc(0.2, 0.1, 0.1, -math.pi / 2, 0)
	ctx.line_to(0.5, 0.1)  # Line to (x,y)
	# Curve(x1, y1, x2, y2, x3, y3)
	ctx.curve_to(0.5, 0.2, 0.5, 0.4, 0.2, 0.8)
	ctx.close_path()

	ctx.set_source_rgb(0.3, 0.2, 0.5)  # Solid color
	ctx.set_line_width(0.02)
	ctx.stroke()

	# Prepare an _in memory_ file system and write the image to a file.
	memfs = MemoryFS()
	with memfs.open("translation.png", "wb") as fout:
		surface.write_to_png(fout)

	del ctx
	surface.finish()
	del surface

	return memfs

# This is horrible. Sorry.
def do_translate(msg):
	# fixed width assumption, or at least maximum constraint
	font_size = 48 
	font_vertical_padding = 3
	lines = msg.splitlines()
	max_cols = len(max(lines, key=len))
	max_lines = msg.count('\n')
	line_extents = []

	# ############################
	# First, we figure out a surface we KNOW is large enough to render the
	# text. This ensures that the text doesn't fall off the edges of the
	# image and confuse our computations.
	# ############################
	WIDTH = max_cols * font_size
	HEIGHT = (max_lines + 1) * (font_size + font_vertical_padding)

	# ############################
	# Now make a surface so we can find the text extents of each line.
	# ############################
	surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, WIDTH, HEIGHT)
	ctx = cairo.Context(surface)

	#ctx.select_font_face("DejaVu Sans Mono", cairo.FONT_SLANT_NORMAL, \
	#	cairo.FONT_WEIGHT_NORMAL)
	ctx.set_font_face(MASTIS_FONT_FACE)
	ctx.set_font_size(font_size)

	# We act as if we draw the lines over each other cause it doesn't matter
	# for extent calculation. But we move to the middle of the surface for
	# safety.
	for line in lines:
		ctx.move_to(0, HEIGHT / 2)
		line_extents.append([line, ctx.text_extents(line)])

	# Clean up cause we're dumping this surface and context now!
	del ctx
	surface.finish()
	del surface

	# ############################
	# Recompute the correct size of the surface.
	# ############################
	WIDTH = 0
	HEIGHT = 0
	for line_extent in line_extents:
		extent = line_extent[1]
		WIDTH = max(math.ceil(extent.width), WIDTH)
		# TODO: Computation of height needs a reckoning.
		HEIGHT += max(font_size, math.ceil(extent.height)) + \
					font_vertical_padding
	WIDTH = math.ceil(WIDTH)
	HEIGHT = math.ceil(HEIGHT)

	# ############################
	# Now finally we can reallocate a new surface that is exactly what we need
	# to draw the text.
	# ############################

	surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, WIDTH, HEIGHT)
	ctx = cairo.Context(surface)

	ctx.set_source_rgba(1.0, 1.0, 1.0, 1.0) # background: white
	ctx.rectangle(0, 0, WIDTH, HEIGHT)
	ctx.fill()

	# ############################
	# And finally render the text!
	# ############################
	#ctx.select_font_face("DejaVu Sans Mono", cairo.FONT_SLANT_NORMAL, \
	#	cairo.FONT_WEIGHT_NORMAL)
	ctx.set_font_face(MASTIS_FONT_FACE)
	ctx.set_font_size(font_size)
	ctx.set_source_rgba(0, 0, 0, 1) # foreground font color: black

	# TODO: When it comes time to deal with the y_bearing and whatnot, there
	# will be a reckoning in this snippet of code... Kerning is probably
	# screwed as well.
	dx = 0
	dy = 0
	for line_extent in line_extents:
		line = line_extent[0]
		extent = line_extent[1]
		dy += font_size # math.ceil(extent.height) + y_bearing... etc etc
		ctx.move_to(dx, dy)
		ctx.show_text(line)
		dy += font_vertical_padding

	ctx.stroke()

	# ############################
	# Prepare an _in memory_ file system and write the image to a file.
	# ############################
	memfs = MemoryFS()
	with memfs.open("translation.png", "wb") as fout:
		surface.write_to_png(fout)

	del ctx
	surface.finish()
	del surface

	return memfs

client = discord.Client()

@client.event
async def on_ready():
	print(f"client.user: {client.user} is ready!")

	guild = discord.utils.get(client.guilds, name = GUILD_NAME)
	if not guild:
		print(" Sorry! no valid guilds found!")
		return

	print(f"{client.user} is connected to (at least) the guild:\n"
		f" - {guild.name}")

	# what members can the bot see?
	members = '\n - '.join([member.name for member in guild.members])
	print(f'Viewable Guild Members:\n - {members}')

	# What users can the bot see?
	users = '\n - '.join([user.name for user in client.users])
	print(f'Viewable Users:\n - {users}')


@client.event
async def on_message(message):
	# Ensure that the bot cannot reply to itself!
	if message.author == client.user:
		return

	# TODO: If the user left the guild, this is a User type, not a Member type.
	# Figure out the consequences of that.
	author_nickname = message.author.display_name

	print(f"-- Observed message: \n"
		f" - guild: {message.guild.name}\n"
		f" - channel: #{message.channel.name}\n"
		f" - author: {message.author.display_name}({message.author.name})")

	# Ignore if not from the right guild.
	if message.guild.name != GUILD_NAME:
		print(f" * Ignoring because not in guild: #{GUILD_NAME}");
		return

	# Ignore if not from the right channel.
	if message.channel.name != CHANNEL_NAME:
		print(f" * Ignoring because not in channel: #{CHANNEL_NAME}");
		return

	print(f" - content: '{message.content}'")

	# If there is cause to respond, do something.
	# TODO: Very primitive for now.
	p = re.compile(r'^\s*mastis-bot: (?P<cmd>\w+(-\w+)*)\s*(?P<arg>.*)$')
	query = p.search(message.content.lower())
	cmd = query.group('cmd')
	arg = query.group('arg')
	if arg is not None:
		arg = arg.strip()
	
	if query:
		print(f" [Sending response]")

		if "help" in cmd:
			response = f"{author_nickname}:\nInstructions:\n" \
				"The basic format for asking me to do something is:\n" \
				"mastis-bot: <cmd>\n" \
				"The supported commands so far are:\n" \
				"help, aunka, test-image\n" \
				"An example command is:\n" \
				"mastis-bot: help" 
			print(f"   - '{response}'")
			await message.channel.send(response)

		elif "xlate" in cmd:
			kt = ku.KiltaTokenizer()
			mastis_text = kt.romanized_to_mastis(arg.strip())
			dedented = tw.dedent(mastis_text).strip()
			xlate = tw.fill(dedented, width=40)
			response = f"{author_nickname} wrote:\n"

			# Read the file from the in memory FS and dump it to discord.
			memfs = do_translate(xlate)
			with memfs.open('translation.png', 'rb') as fin:
				await message.channel.send(response, \
					file=discord.File(fin, 'translation.png'))
			memfs.close()

		elif "test-cairo" in cmd:
			response = f"{author_nickname}: Ok!"
			print(f"   - '{response}'")
			# Read the file from the in memory FS and dump it to discord.
			memfs = do_cairo()
			with memfs.open('translation.png', 'rb') as fin:
				await message.channel.send(response, \
					file=discord.File(fin, 'translation.png'))
			memfs.close()

		elif "aunka" in cmd:
			response = f"{author_nickname}: Today's date is **{do_aunka()}**."
			print(f"   - '{response}'")
			await message.channel.send(response)

		elif "test-image" in cmd:
			response = f"{author_nickname}: Sending test image!"
			print(f"   - '{response}'")

			with open('/tmp/kilta.png', 'rb') as fp:
				await message.channel.send(response, \
					file=discord.File(fp, 'translation.png'))

		else:
			response = f"{author_nickname}: I don't understand the request: " \
						f"'{cmd}'"
			print(f"   - '{response}'")
			await message.channel.send(response)

client.run(TOKEN)




