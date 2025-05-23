# References:
# https://realpython.com/how-to-make-a-discord-bot-python/
# https://discordpy.readthedocs.io/en/latest/api.html
# https://stackoverflow.com/questions/53693209/get-message-id-of-the-message-sent-by-my-bot
# https://stackoverflow.com/questions/61553424/how-to-make-a-bot-edit-its-own-message-in-discord-py
# https://zetcode.com/gfx/pycairo/
# https://pycairo.readthedocs.io/en/latest/reference/index.html
# https://heuristically.wordpress.com/2011/01/31/pycairo-hello-world/
# https://stackoverflow.com/questions/32321216/making-a-memory-only-fileobject-in-python-with-pyfilesystem
# https://docs.pyfilesystem.org/en/latest/interface.html
# https://pymotw.com/2/textwrap/
# https://fonttools.readthedocs.io/en/latest/index.html
# https://howchoo.com/g/ywi5m2vkodk/working-with-datetime-objects-and-timezones-in-python
# discord API upgrade with intents caused me to find these next 3 links.
# https://discordpy.readthedocs.io/en/latest/intents.html
# https://discordpy.readthedocs.io/en/latest/api.html#discord.Intents
# https://discordpy.readthedocs.io/en/stable/api.html#channels
# https://stackoverflow.com/questions/70920148/pycord-message-content-is-empty
# https://stackoverflow.com/questions/66648995/how-to-set-a-timer-in-discord-py-while-enabling-other-codes
#
# Crappy instructions to install:
# sudo apt install python3-dotenv
# pip3 install -U discord.py
# pip3 install -U fs
# pip3 install -U pycairo
# pip3 install -U fonttools
# python3 mastis-bot.py

import os
import re
import datetime as dt
import pytz
import discord
import asyncio
import math
import cairo
import textwrap as tw
from dotenv import load_dotenv
from datetime import date
from fs.memoryfs import MemoryFS
import font_helper as fh
import kilta_utils as ku
import kilta_date as kd
import kilta_font as kf
import archive as ardb

load_dotenv()

# Found in the unchecked in .env file that must be in the cwd of the
# running script...
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_NAME = os.getenv("DISCORD_GUILD_NAME")
CHANNEL_NAME = os.getenv("DISCORD_CHANNEL_NAME")
MASTIS_FONT = os.path.abspath(os.getenv("MASTIS_FONT"))


# ############################
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

# ############################
def do_layout_test(self):
  pass

# ############################
# This is horrible. Sorry.
def do_translate(self, msg):
  # fixed width assumption, or at least maximum constraint
  font_size = 30
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
  #  cairo.FONT_WEIGHT_NORMAL)
  ctx.set_font_face(self.kilta_font.get_cairo_font_face())
  ctx.set_font_size(font_size)
  # font_extents is (ascent, descent, height, max_x_advance, max_y_advance)
  font_extents = ctx.font_extents()

  # We act as if we draw the lines over each other cause it doesn't matter
  # for extent calculation. But we move to the middle of the surface for
  # safety.
  for line in lines:
    ctx.move_to(0, HEIGHT / 2)
    glyph_line = self.kilta_font.layout_line(ctx, line, font_size)
    # Note I still store the old 'line' here too. I'll need it later
    # when doing the pen position.
    line_extents.append([line, ctx.glyph_extents(glyph_line)])

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
  # TODO: in the next line, 3 is Wrong(tm). Need to figure out the x_advance
  # of the last character on the longest line above and use that here.
  WIDTH = math.ceil(WIDTH + 3)
  # ..and add font's average descent to entail the last line's descenders.
  HEIGHT = math.ceil(HEIGHT + font_extents[1])

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
  #  cairo.FONT_WEIGHT_NORMAL)
  ctx.set_font_face(self.kilta_font.get_cairo_font_face())
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
    # NOTE: ctx knows the current pen position which is why I need to
    # re-layout the line right here again.
    glyph_line = self.kilta_font.layout_line(ctx, line, font_size)
    ctx.show_glyphs(glyph_line) # Already glyphs
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

# ############################
def get_nick(message):
  # TODO: If the user left the guild, this is a User type, not a Member
  # type. Figure out the consequences of that.
  return message.author.display_name

# ############################
class MastisBotClient(discord.Client):
  # Inherited API:
  # https://discordpy.readthedocs.io/en/latest/api.html#client

  # ###################################################################
  # Class Attributes
  # ###################################################################
  # Key: A user message id, Value: the message id mastis_bot created
  # for the response.
  bot_replies = {}

  # Used for iterative testing of bot message editing.
  # TODO: It is not possible to edit image attachement in Discord yet. 
  # So this test code is commented out until it works and I can continue.
  target_message_id = None

  # ###################################################################
  # Constructor
  # ###################################################################
  def __init__(self, font_path):
    intents = discord.Intents.all()
    discord.Client.__init__(self,intents=intents)
    # Herein we set up the ability to get a cairo font face and
    # how to layout the KiltaFont with kerning, etc.
    self.kilta_font = kf.KiltaFont(font_path)
    # Set up the arhive database
    self.archivingp = False
    self.archive_db = ardb.ArchiveDB("kilta_guild_archive.db")
    self.archive_db.open()
    self.archive_db.init()

  # ###################################################################
  # Utility Functions
  # ###################################################################

  # ############################
  # NOTE: This function is on hold for now. Discord doesn't yet allow
  # editing of attached images which is the primary reason for this
  # function's existence.
  async def send_or_edit_response(self, initiating_message, response, \
                    attachment):
    if attachment:
      memfs, filename, dfilename = attachment
      with memfs.open(filename, 'rb') as fin:
        rmsg = await initiating_message.channel.send(response, \
          file=discord.File(fin, dfilename))
      memfs.close()
      return rmsg

    rmsg = await initiating_message.channel.send(response)
    return rmsg

  # ###################################################################
  # mastis_bot Command Handlers
  # ###################################################################

  # ############################
  async def command_help(self, message, arg):
    author_nickname = get_nick(message)
    response = f"**{author_nickname}**:\n" \
      "A command must start with a period.\n" \
      "The supported commands are:\n" \
      "**.help**  - This help\n" \
      "**.aunka** - Today's aunka in Romanized Kílta\n" \
      "**.date** - Today's date in Romanized Kílta\n" \
      "**.m Romanized Kílta** - " \
        "Translate utterance to **Mastis**\n" \
      "An example command is:\n" \
      ".m Suríli."
    print(f"   -|{response.rstrip()}")
    rmsg = await self.send_or_edit_response(message, response, None)
    print(f"   - Response message id: {rmsg.id}")
    return rmsg

  # ############################
  async def command_aunka(self, message, arg):
    print(f" [Sending response]")
    author_nickname = get_nick(message)
    kaura, olta, aunka, tun = kd.compute_kilta_date()
    response = f"**{author_nickname}**: Today's aunka is **{aunka}**."
    print(f"   -|{response.rstrip()}")
    rmsg = await self.send_or_edit_response(message, response, None)
    print(f"   - Response message id: {rmsg.id}")
    return rmsg

  # ############################
  async def command_date(self, message, arg):
    print(f" [Sending response]")
    author_nickname = get_nick(message)
    kaura, olta, aunka, tun = kd.compute_kilta_date()
    kilta_date = f"{kaura} {olta} {aunka} {tun}"
    response = f"**{author_nickname}**: Today's date is **{kilta_date}**."
    print(f"   -|{response.rstrip()}")
    rmsg = await self.send_or_edit_response(message, response, None)
    print(f"   - Response message id: {rmsg.id}")
    return rmsg

  # ############################
  # TODO: It is not possible to edit image attachement in Discord yet. 
  # So this test code is commented out until it works and I can continue.
  #async def command_set_target(self, message, arg):
  #  print(f" [Sending response]")
  #  author_nickname = get_nick(message)
  #  response = f"{author_nickname}: This is the target message."
  #  rmsg = await self.send_or_edit_response(message, response, None)
  #  print(f"   - Response message id: {rmsg.id}")
  #  self.target_message_id = rmsg.id
  #  return rmsg

  # ############################
  # TODO: It is not possible to edit image attachement in Discord yet. 
  # So this test code is commented out until it works and I can continue.
  #async def command_edit_target(self, message, arg):
  #  author_nickname = get_nick(message)
  #  if self.target_message_id:
  #    print("  - Attempting to edit target message!")
  #    msg = await message.channel.fetch_message(self.target_message_id)
  #    print(f"  - Fetched: {msg}")
  #    ret = await msg.edit(content="Message edited!")
  #    print(f"  - Edited: {ret}")
  #  return None

  # ############################
  async def command_test_cairo(self, message, arg):
    # Testing is streaming a dynamically created svg image.
    print(f" [Sending response]")
    author_nickname = get_nick(message)
    response = f"{author_nickname}: Ok!"
    print(f"   -|{response.rstrip()}")
    print( "   -|[image]")
    # Read the file from the in memory FS and dump it to discord.
    memfs = do_cairo()
    rmsg = await self.send_or_edit_response(message, response, \
      (memfs, 'translation.png', 'translation.png'))
    print(f"   - Response message id: {rmsg.id}")
    return rmsg

  # ############################
  async def command_m(self, message, arg):
    print(f" [Sending response]")
    author_nickname = get_nick(message)
    max_len = 2048 # Just a bad hack to prevent overflow problems...
    truncated_arg = (arg[:max_len] + '....') if len(arg) > max_len else arg

    kt = ku.KiltaTokenizer()

    mastis_text = kt.romanized_to_mastis(truncated_arg.strip())
    dedented = tw.dedent(mastis_text).strip()
    # NOTE: It turns out discord will use HTML tags to shrink larger
    # images (like say of text with mnore columns). So, we keep this at
    # 40 columns in order to keep the width generally ok for the image
    # and hopefully there isn't too much shrinking based on height.
    # I haven't run into any yet, but I'm sure we will at some point.
    xlate = tw.fill(dedented, width=40)
    response = f"**{author_nickname}** wrote:\n"
    print(f"   -|{response.rstrip()}")
    print( "   -|[image]")

    # Read the file from the in memory FS and dump it to discord.
    memfs = do_translate(self, xlate)
    rmsg = await self.send_or_edit_response(message, response, \
      (memfs, 'translation.png', 'translation.png'))
    print(f"   - Response message id: {rmsg.id}")
    return rmsg

  # ############################
  async def command_test_history(self, message, arg):
    # Get a time 10 years go from today.
    utc_now = dt.datetime.now(dt.timezone.utc).timestamp()
    timestamp = utc_now - (86400 * 365) * 10
    timepoint = dt.datetime.fromtimestamp(timestamp, tz=dt.timezone.utc)

    print(f" [Sending response]")
    author_nickname = get_nick(message)
    response = f"**{author_nickname}**: First three messages in this channel since {timestamp} epoch seconds!\n"

    # Retrieve the messages.
    hist_messages = \
      [msg async for msg in message.channel.history(limit=3, after=timepoint)]

    rbody = ""
    for hmsg in hist_messages:
      rbody += f"{hmsg.created_at}: {hmsg.author} - {hmsg.content}\n"

    response += rbody;

    print(f"   -|{response.rstrip()}")
    rmsg = await self.send_or_edit_response(message, response, None)
    print(f"   - Response message id: {rmsg.id}")
    return rmsg

  # ############################
  async def command_unknown(self, message, cmd, arg):
    print(f" [Sending response]")
    author_nickname = get_nick(message)
    response = f"{author_nickname}: I don't understand the request: " \
          f"'.{cmd}'"
    print(f"   -|{response}")
    rmsg = await self.send_or_edit_response(message, response, None)
    print(f"   - Response message id: {rmsg.id}")
    return rmsg

  # ###################################################################
  # Periodic functions in a timer coroutine
  # ##################################################################

  # ############################
  # Since this is a coroutine, this won't do work unless it it capable of
  # doing work.
  async def periodic_archive(self, guild, seconds, channels_to_backup):
    print(f"Channels expected to be backed up: {channels_to_backup}")

    central_timezone = pytz.timezone('America/Chicago')
    all_channels = [ channel for channel in guild.channels ]

    # 1. Filter which channels we're going to backup.
    archive_channels = \
      [ channel for channel in all_channels \
          if channel.name in channels_to_backup ]

    print(f"Archiving channels: {[chan.name for chan in archive_channels]}")

    if len(channels_to_backup) != len(archive_channels):
      print("ERROR: Can't backup some expected channels! Programmer error!")
      os.sys.exit(1)

    # Get the bot channel for updates during backup.
    nivaután = \
      discord.utils.find(lambda c: c.name == 'nivaután', guild.channels)

    if len(archive_channels) == 0:
      #await nivaután.send("mastis-bot: No channels to archive!")
      print("No channels to archive!")
      return

    # TODO: Technically this won't return, is this ok as a coroutine?
    # Walk each channel and back it up.
    iter = 0
    while (True):
      archive_stats = dict()
      total_scan_seconds = 0
      total_messages_archived = 0

      now_local = dt.datetime.now(central_timezone)
      print(f"Performing Archive Scan at America/Chicago time: {now_local}...")

      for channel in archive_channels:
        dbmsgs = []
        rbody = f"--| **Archive of: {channel.name}, Iter: {iter}**\n"

        scan_start_timestamp = dt.datetime.now(dt.timezone.utc).timestamp()

        # First, we get the current synctime for the channel, everything
        # AFTER this we're gonna store into the DB.
        (after_timepoint_timestamp, after_timepoint) = \
          self.archive_db.get_synctime(guild.name, channel.name)

        # Then, we get the time we're going "up to", everything
        # BEFORE this we're gonna store into the DB.
        (before_timepoint_timestamp, before_timepoint) = \
          self.archive_db.generate_new_synctime()

        rbody += f"  |> After: {after_timepoint}, Before: {before_timepoint}\n"

        # TODO: There is a race condition here if a message is exactly on either
        # of the timepoints.. it can get lost in that case!
        hist_messages = \
          [msg async for msg in channel.history(limit=None,
                                                after=after_timepoint,
                                                before=before_timepoint,
                                                )]

        # We assume the same guild and channel for replies
        # (though this absolutely doesn't have to be true)
        for hmsg in hist_messages:
          # rbody += f"  |> {hmsg.created_at}: {hmsg.author}\n"

          ref_id = -1
          if hmsg.reference and hmsg.reference.message_id:
            ref_id = hmsg.reference.message_id

          # Collect any reaction emojis if present.
          reaction_emojis = \
            " ".join([str(reaction.emoji) for reaction in hmsg.reactions])

          dbmsgs.append(
            ardb.ArchiveMsg(
              guild.name,
              channel.name,
              hmsg.id,
              hmsg.created_at,
              hmsg.author.name,
              hmsg.author.display_name,
              hmsg.content,
              ref_id,
              reaction_emojis))

        # If any messages arrived after the time range we picked, no big deal
        # we will catch them next time.
        stored = self.archive_db.insert(guild.name, channel.name, \
          dbmsgs, before_timepoint_timestamp)
        scan_stop_timestamp = dt.datetime.now(dt.timezone.utc).timestamp()

        total_messages_archived = total_messages_archived + stored

        archive_stats[channel.name] = scan_stop_timestamp - scan_start_timestamp
        rbody += f"  |> Channel messages archived: {stored}\n"
        rbody += f"  |> Channel scan seconds: {archive_stats[channel.name]}"
        total_scan_seconds = total_scan_seconds + archive_stats[channel.name]
        print(rbody)

      rbody = f"  |> Total messages archived: {total_messages_archived}\n"
      rbody += f"  |> Total scan seconds: {total_scan_seconds}"
      print(rbody)

      # Now sleep...

      # Account the time it took to do the work and subtract it from
      # how much time I must wait. If I blew up my time allotment, then wait
      # arbitrarily twice as much as the time it took and see if it gets faster
      # later.
      wait_seconds = seconds - int(total_scan_seconds)
      if wait_seconds < 0:
        wait_seconds = int(total_scan_seconds) * 2

      print(f"Completed archive scan. Sleeping {wait_seconds} second(s)!")
      await asyncio.sleep(wait_seconds)
      iter += 1

  # ###################################################################
  # Discord Client Interface
  # ###################################################################

  # ############################
  async def on_ready(self):
    # Archive every 4 hours.
    periodic_archive_seconds = 60 * 60 * 4

    print(f"self.user: {self.user} is ready!")

    guild = discord.utils.get(self.guilds, name = GUILD_NAME)
    if not guild:
      print(" Sorry! no valid guilds found!")
      return

    print(f"{self.user} is connected to (at least) the guild:\n"
      f" - {guild.name}")

    # what channels can the bot see?
    all_channels = [ channel for channel in guild.channels ]
    print('Viewable Channels:')
    for channel in all_channels:
      print(f" - {channel.name}")

    # what members can the bot see?
    members = '\n - '.join([member.name for member in guild.members])
    print(f'Viewable Guild Members:\n - {members}')

    # What users can the bot see?
    users = '\n - '.join([user.name for user in self.users])
    print(f'Viewable Users:\n - {users}')

    # Inform the channel the bot is up.
    nivaután = \
      discord.utils.find(lambda c: c.name == 'nivaután', guild.channels)

    # await nivaután.send(f"**Mastis Bot is Ready!**")

    # Now, set up a coroutine that runs forever and periodically and
    # backs up requested channels to the ArchiveDB database.
    channels_to_backup = [ \
      "kíltui", "updates", "proposals", "grammar-and-vocab", \
      ]

    # Only start coroutine if it isn't already runniung since this on_ready()
    # can be called more than once in the life of a client.
    if self.archivingp == False:
      self.archivingp = True
      await self.periodic_archive(guild, periodic_archive_seconds, \
              channels_to_backup)

  # ############################
  async def on_message_delete(self, message):
    # Bot doesn't care if it deletes its own message.
    if message.author == self.user:
      return

    author_nickname = get_nick(message)

    print("-- Message deleted:")
    print(f" - author: {author_nickname}({message.author.name})")

    # If the deleted message happen to be one that initiated a bot
    # reply, we remove the link between it and the reply, thereby the
    # bot forgets how to edit its reply. We don't delete the bot reply
    # (at this time).
    val = self.bot_replies.pop(message.id, None)
    if val:
      print(f"%-> Removed message from cache: {message.id} -/-> {val}!")
  
  # TODO: Handle bulk message deletes later.

  # ############################
  async def on_message_edit(self, before, after):
    # Ensure that the bot cannot reply to itself!
    if before.author == self.user or after.author == self.user:
      return

    # TODO: Keep track of the message ids that contained xlate commands and
    # the messages I generated in response to it. If the original message
    # changed, then attempt to edit the message I originally sent in place
    # with the new translations.

    print("-- Message edited:")
    print(f" Before: ({before.author.display_name}, msg id: {before.id})")
    print(f"  - {before.content}")
    print(f" After: ({after.author.display_name}, msg id: {after.id})")
    print(f"  - {after.content}")

  # ############################
  async def on_message(self, message):
    # Ensure that the bot cannot reply to itself!
    if message.author == self.user:
      return

    print(f"-- Observed message (id: {message.id}): \n"
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

    # See if the message is a command to the bot...
    p = re.compile(r'^\s*[.](?P<cmd>\w+(-\w+)*)\s*(?P<arg>.*)$')
    query = p.search(message.content.lower())
    if not query:
      print(" [No query detected. Doing nothing!]")
      return

    cmd = query.group('cmd')
    arg = query.group('arg')
    if arg is not None:
      arg = arg.strip()
  
    if not query:
      return

    if cmd == "help":
      rmsg = await self.command_help(message, arg)
    elif cmd == "aunka":
      rmsg = await self.command_aunka(message, arg)
    elif cmd == "date":
      rmsg = await self.command_date(message, arg)
    elif cmd == "test-cairo":
      rmsg = await self.command_test_cairo(message, arg)
    elif cmd == "m":
      rmsg = await self.command_m(message, arg)
    # Use this as a starting point for periodically getting chat history from
    # these channels:
    # #kíltui, #proposals, #grammar-and-vocab
    # and then storing them in a sqlite3 db. Get reactions too.
    #elif cmd == "test-history":
    #  rmsg = await self.command_test_history(message, arg)

    # TODO: It is not possible to edit image attachement in Discord yet. 
    # So this test code is commented out until it works and I can continue.
    #elif cmd == "set-target":
    #  rmsg = await self.command_set_target(message, arg)
    #elif cmd == "edit-target":
    #  rmsg = await self.command_edit_target(message, arg)

    #elif cmd == "history":
    #  response = " - Bot history:\n"
    #  for initial, reply in self.bot_replies.items():
    #    response += f"   - Initial: {initial} -> reply: {reply}\n"
    #  response += "Done."
    #  print(response)
    #  rmsg = await message.channel.send(response)
    else:
      rmsg = await self.command_unknown(message, cmd, arg)

    # Associate the incoming message with the response so we can edit
    # it later if the original author which prompted the response 
    # edits their message.
    if rmsg:
      self.bot_replies[message.id] = rmsg.id
      print(f"%-> Added to message cache: {message.id} -> {rmsg.id}")
    else:
      print("%-> No reply to add to cache!")

# ############################
def main():
  print("Starting mastis_bot...")
  client = MastisBotClient(MASTIS_FONT)
  client.run(TOKEN)
  return 0

# ############################
if __name__ == '__main__':
  os.sys.exit(main())




