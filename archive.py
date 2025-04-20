#! /usr/bin/env python3

import os
import sqlite3
import datetime as dt
import pytz
import gzip

# Message dates are stored as UTC time in ISO string Format.
# The synctime is stored as a Unix epoch integer in UTC format.

# ###################
def doit_iso():
  # Install adapters for python3 and sqlite3 to deal with datetimes as they
  # enter and exit the DB representation. I'm not entirely sure this is
  # all exactly right at this time...

  # ############################
  def adapt_date_iso(val):
      """Adapt datetime.date to ISO 8601 date."""
      # print(f"adapt_date_iso: {val} has type of {type(val)}")
      return val.isoformat()

  # ############################
  def adapt_datetime_iso(val):
      """Adapt datetime.datetime to timezone-naive ISO 8601 date."""
      # print(f"adapt_datetime_iso: {val} has type of {type(val)}")
      return val.isoformat()

  # ############################
  def adapt_datetime_epoch(val):
      """Adapt datetime.datetime to UNIX timestamp."""
      # print(f"adapt_datetime_epoch: {val} has type of {type(val)}")
      return int(val.timestamp())

  sqlite3.register_adapter(dt.date, adapt_date_iso)
  # NOTE: We must choose one between these two for DATE types.
  # We want to store ISO format for messages because it is easier to read
  # and we don't use them in SQL queries. But the synctime field is an
  # INTEGER field and we store a timestamp in there.
  sqlite3.register_adapter(dt.datetime, adapt_datetime_iso)
  # sqlite3.register_adapter(dt.datetime, adapt_datetime_epoch)

  # ############################
  def convert_date(val):
      """Convert ISO 8601 date to datetime.date object."""
      # print(f"convert_date: {val} has type of {type(val)}")
      return dt.date.fromisoformat(val.decode())

  # ############################
  def convert_datetime(val):
      """Convert ISO 8601 datetime to datetime.datetime object."""
      # print(f"convert_datetime: {val} has type of {type(val)}")
      return dt.datetime.fromisoformat(val.decode())

  # ############################
  def convert_timestamp(val):
      """Convert UNIX epoch timestamp to datetime.datetime object."""
      # print(f"convert_timestamp: {val} has type of {type(val)}")
      return dt.datetime.fromtimestamp(int(val))

  sqlite3.register_converter("date", convert_date)
  sqlite3.register_converter("datetime", convert_datetime)
  sqlite3.register_converter("timestamp", convert_timestamp)

doit_iso()


class ArchiveMsg:
  # NOTE: The only reason this class exists is to remove an ordering
  # constraint between the user of the ArchiveDB and the ArchiveDB itself
  # wrt the values in an insertion.

  # ############################
  def __init__(self,  guild_name = "UnknownGuildName",
                      chan_name = "UnknownChannelName", 
                      msg_id = 0,
                      msg_created_at =
                        dt.datetime(1970, 1, 1, 0, 0, 0,
                         tzinfo=dt.timezone.utc).timestamp(),
                      msg_author = "UnknownAuthor",
                      msg_display_name = "UnknownDisplayName",
                      msg_content = "UnknownContent",
                      msg_reference_id = 0,
                      msg_emoji_reactions = "UnknownEmojiReactions"):
    self.guild_name = guild_name
    self.chan_name = chan_name
    self.msg_id = msg_id
    self.msg_created_at = msg_created_at
    self.msg_author = msg_author
    self.msg_display_name = msg_display_name
    self.msg_content = msg_content
    self.msg_reference_id = msg_reference_id
    self.msg_emoji_reactions = msg_emoji_reactions

  # ############################
  def values_tuple(self):
    # Return a tuple ordered for insertion in the the DB.
    return (
      self.guild_name,
      self.chan_name,
      self.msg_id,
      self.msg_created_at,
      self.msg_author,
      self.msg_display_name,
      self.msg_content,
      self.msg_reference_id,
      self.msg_emoji_reactions,
    )

class ArchiveDB:
  # DATE fields are UTC time stored in ISO String Format.
  sql_create_table_message = '''
    CREATE TABLE IF NOT EXISTS message (
      guild_name TEXT NOT NULL,
      chan_name TEXT NOT NULL,
      msg_id INTEGER NOT NULL,
      msg_created_at DATE NOT NULL,
      msg_author TEXT NOT NULL,
      msg_display_name TEXT NOT NULL,
      msg_content TEXT NOT NULL,
      msg_reference_id INTEGER NOT NULL,
      msg_emoji_reactions TEXT NOT NULL,
      PRIMARY KEY (guild_name, chan_name, msg_id)
    )
    '''
  # The field synched_upto_utc_date is a unix timestamp in UTC time, so INTEGER
  sql_create_table_synctime = '''
    CREATE TABLE IF NOT EXISTS synctime (
      guild_name TEXT NOT NULL,
      chan_name TEXT NOT NULL,
      synched_upto_utc_date INTEGER NOT NULL,
      PRIMARY KEY (guild_name, chan_name)
    )
    '''
  sql_select_channel_synctime = '''
    SELECT synched_upto_utc_date
    FROM synctime 
    WHERE guild_name = ? AND chan_name = ?
    '''
  # TODO: This is a nop if the time goes backwards....
  # Decide if this is what I actually want. Delete where clause if not.
  sql_insert_or_update_channel_synctime = '''
    INSERT INTO synctime(guild_name, chan_name,synched_upto_utc_date)
      VALUES(?, ?, ?)
      ON CONFLICT(guild_name, chan_name)
        DO UPDATE SET synched_upto_utc_date=excluded.synched_upto_utc_date
          WHERE excluded.synched_upto_utc_date > synctime.synched_upto_utc_date
    '''
  sql_insert_msg = '''
    INSERT INTO message(
      guild_name,
      chan_name, 
      msg_id, 
      msg_created_at,
      msg_author,
      msg_display_name,
      msg_content,
      msg_reference_id,
      msg_emoji_reactions
    )
    VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
    '''

  # ############################
  def __init__(self, db_file="archive.db"):
    self.db_file = db_file
    self.conn = None
    self.cursor = None

    # We care about two timezones:
    self.central_timezone = pytz.timezone('America/Chicago')
    self.utc_timezone = pytz.timezone("UTC")

    # Kilta Epoch is "Sept 5, 2001 America/Chicago", sadly we can't use this
    # because if we try to search stuff in Discord before Discord's epoch
    # start, we get an API error. Like WTF, you know?

    # Discord Start Epoch is "Jan 1, 2015 UTC" (gotten by binary search)
    self.utc_discord_epoch_start = \
      dt.datetime(2015, 1, 1, 0, 0, 0, tzinfo=self.utc_timezone)

    # ....and finally to a UTC Unix timestamp with seconds resolution.
    self.utc_discord_epoch_start_timestamp = \
      int(self.utc_discord_epoch_start.timestamp())

  # ############################
  def open(self):
    # Open only once.
    if self.conn == None:
      self.conn = sqlite3.connect(self.db_file)
      self.cursor = self.conn.cursor()

  # ############################
  def commit(self):
    self.open()
    self.conn.commit()

  # ############################
  def init(self):
    self.open()
    self.cursor.execute(self.sql_create_table_message)
    self.cursor.execute(self.sql_create_table_synctime)
    self.commit()

  # ############################
  def synctime_utc_now(self):
    return dt.datetime.now(dt.timezone.utc)

  def set_synctime(self, guild_name, chan_name, new_synctime):
    # NOTE: Specifically no db commit in this function so we can do the
    # message list and time insertion in one transaction.
    self.open()

    # NOTE: This stores an INTEGER unix timestamp in UTC time.
    self.cursor.execute(self.sql_insert_or_update_channel_synctime, \
      (guild_name, chan_name, new_synctime))

  # ############################
  def get_synctime(self, guild_name, chan_name):
    self.open()

    self.cursor.execute(self.sql_select_channel_synctime, \
      (guild_name, chan_name,));

    rows = self.cursor.fetchall()
    if len(rows) == 0:
      synctime_timestamp = self.utc_discord_epoch_start_timestamp
      self.set_synctime(guild_name, chan_name, synctime_timestamp)
      return \
        ( synctime_timestamp,
          dt.datetime.\
          fromtimestamp(synctime_timestamp).\
          astimezone(self.utc_timezone)
        )

    # There is only ever one row, so verify that.
    if len(rows) > 1:
      print(f"Error: synctime multiple rows for a channel: {rows}")
      os.sys.exit(1)

    # synctime present in the database.
    row = rows[0]
    synctime_timestamp = row[0]
    return \
      ( synctime_timestamp,
        dt.datetime.\
        fromtimestamp(synctime_timestamp).\
        astimezone(self.utc_timezone)
      )

  # ############################
  def generate_new_synctime(self):
    # TODO: Ugh, missing time here...
    synctime = dt.datetime.now(dt.timezone.utc)
    return ( int(synctime.timestamp()), synctime )

  # ############################
  def insert(self, guild_name, chan_name, msg_list, new_synctime):
    self.open()

    # This code is setup in a single transaction to all succeed or all fail.
    # It protects against power failure, etc.

    # Step 0: Finalize any pending transaction
    self.commit()
    
    # Step 1: insert all new messages
    for msg in msg_list:
      self.cursor.execute(self.sql_insert_msg, msg.values_tuple())

    # Step 2: update the synctime for this channel
    self.set_synctime(guild_name, chan_name, new_synctime)

    # Step 3: Finally commit the transaction
    self.commit()

    return len(msg_list)

  # ############################
  def close(self):
    if self.conn != None:
      self.commit()
      self.conn.close()
      self.conn = None
      self.cursor = None

  # TODO: Figure out how easy it is to add this so it stores into the DB. 
  # The TEXT datatype will have to go to BLOB.
  # It affects searching the DB, so mabe I should only do it if the space is
  # ACTUALLY a problem.

  # ############################
  def gzip_str(str):
    # returns a bytes object
    return gzip.compress(str.encode())

  # ############################
  def gunzip_bytes_obj(bytes_obj):
    # Returns a string
    return gzip.decompress(bytes_obj).decode()



# ---------------------------------------------------------------------------



def test0():
  now = dt.datetime.now(dt.timezone.utc)
  now_timestamp = int(now.timestamp())
  guild_name = "kílta"
  chan_name = "foobar"
  msgs = [\
    ArchiveMsg(guild_name, chan_name, \
      "0", now, "pkeller_4884", "uhítël", "Hello world", "", ""), \
    ArchiveMsg(guild_name, chan_name, \
      "1", now, "william_annis", "árël", "More Stuff", "", ""), \
    ]
          
  db = ArchiveDB("test.db")
  db.open()
  db.init()

  (utc_time, utc_time_dt) = db.get_synctime(guild_name, chan_name)
  print(f"synctime 0: chan_name: {chan_name}, utc_time: {utc_time}/{utc_time_dt}")

  db.set_synctime(guild_name, chan_name, now_timestamp)
  (utc_time, utc_time_dt) = db.get_synctime(guild_name, chan_name)
  print(f"synctime 1: chan_name: {chan_name}, utc_time: {utc_time}/{utc_time_dt}")

  db.set_synctime(guild_name, chan_name, now_timestamp + 10)
  (utc_time, utc_time_dt) = db.get_synctime(guild_name, chan_name)
  print(f"synctime 2: chan_name: {chan_name}, utc_time: {utc_time}/{utc_time_dt}")
  
  ret = db.insert(guild_name, chan_name, msgs, now_timestamp)
  print(f"{ret} messages inserted.")

  db.close()

  return 0

def main():
  ret = test0()
  return ret

if __name__ == '__main__':
  os.sys.exit(main())

