#! /usr/bin/env python3

import os
import sqlite3
import datetime as dt
import gzip

# TODO: Add datetime converters to shove into UTC format. Ugh.
# The default converters for datetime & sqlite3 got deprecated in python 3.12.

class ArchiveDB:
  sql_create_table_message = '''
    CREATE TABLE IF NOT EXISTS message (
      chan_name TEXT NOT NULL,
      msg_id TEXT NOT NULL,
      msg_utc_date DATE NOT NULL,
      msg_author TEXT NOT NULL,
      msg_author_nick TEXT NOT NULL,
      msg_body TEXT NOT NULL,
      msg_reply_to TEXT NOT NULL,
      msg_reactions TEXT NOT NULL,
      PRIMARY KEY (chan_name, msg_id)
    )
    '''
  sql_create_table_synctime = '''
    CREATE TABLE IF NOT EXISTS synctime (
      chan_name TEXT NOT NULL,
      synched_upto_utc_date DATE NOT NULL,
      PRIMARY KEY (chan_name)
    )
    '''
  sql_select_channel_synctime = '''
    SELECT synched_upto_utc_date FROM synctime WHERE chan_name = ?
    '''
  # TODO: This is a nop if the time goes backwards....
  # Decide if this is what I actually want. Delete where clause if not.
  sql_insert_or_update_channel_synctime = '''
    INSERT INTO synctime(chan_name, synched_upto_utc_date) VALUES(?, ?)
      ON CONFLICT(chan_name)
        DO UPDATE SET synched_upto_utc_date=excluded.synched_upto_utc_date
          WHERE excluded.synched_upto_utc_date > synctime.synched_upto_utc_date
    '''
  sql_insert_msg = '''
    INSERT INTO message(chan_name, msg_id, msg_utc_date, msg_author,
      msg_author_nick, msg_body, msg_reply_to, msg_reactions)
      VALUES(?, ?, ?, ?, ?, ?, ?, ?)
    '''

  def __init__(self, db_file="archive.db"):
    self.db_file = db_file
    self.conn = None
    self.cursor = None
    # Kilta Epoch is Sept 5, 2001 (I assume UTC--document doesn't specify.)
    self.utc_kilta_epoch_start = \
      dt.datetime(2001, 9, 5, 0, 0, 0, tzinfo=dt.UTC)

  def open(self):
    # Open only once.
    if self.conn == None:
      self.conn = sqlite3.connect(self.db_file)
      self.cursor = self.conn.cursor()

  def commit(self):
    self.open()
    self.conn.commit()

  def init(self):
    self.open()
    # create all tables
    self.cursor.execute(self.sql_create_table_message)
    self.cursor.execute(self.sql_create_table_synctime)
    self.commit()

  def synctime_utc_now(self):
    return dt.datetime.now(dt.timezone.utc)

  def set_synctime(self, chan_name, new_synctime):
    self.open()

    # print("inserting new synctime")
    self.cursor.execute(self.sql_insert_or_update_channel_synctime, \
      (chan_name, new_synctime))

    # NOTE: Specifically no commit here.

  def get_synctime(self, chan_name):
    self.open()

    self.cursor.execute(self.sql_select_channel_synctime, (chan_name,));
    rows = self.cursor.fetchall() # for row in rows: to iterate
    if len(rows) == 0:
      self.set_synctime(chan_name,self.utc_kilta_epoch_start)
      return self.utc_kilta_epoch_start

    # There is only ever one row, so verify that.
    if len(rows) > 1:
      print(f"Error: synctime multiple rows for a channel: {rows}")
      os.sys.exit(1)

    # print("Retrieving present synctime")
    row = rows[0]
    return row[0]

  def insert(self, chan_name, msg_list, new_synctime):
    self.open()

    # This code is setup in a single transaction to all succeed or all fail.
    # It protects against power failure, etc.

    # Step 0: Finalize any pending transaction
    self.commit()
    
    # Step 1: insert all new messages
    for msg in msg_list:
      self.cursor.execute(self.sql_insert_msg,
        (chan_name,) + tuple(msg))

    # Step 2: update the synctime for this channel
    self.set_synctime(chan_name, new_synctime)

    # Step 3: Finally commit the transaction
    self.commit()

    return len(msg_list)

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

  def gzip_str(str):
    # returns a bytes object
    return gzip.compress(str.encode())

  def gunzip_bytes_obj(bytes_obj):
    # Returns a string
    return gzip.decompress(bytes_obj).decode()



# ---------------------------------------------------------------------------



def test0():
  now = dt.datetime.now(dt.timezone.utc)
  chan = "foobar"
  msgs = [  ["0", now, "pkeller_4884", "uhítël", "Hello world", "", ""], \
            ["1", now, "william_annis", "árël", "More Stuff", "", ""], \
    ]
          
  db = ArchiveDB("test.db")
  db.open()
  db.init()

  chan = "foobar"
  utc_time = db.get_synctime(chan)
  print(f"synctime 0: chan: {chan}, utc_time: {utc_time}")

  utc_time = db.get_synctime(chan)
  print(f"synctime 1: chan: {chan}, utc_time: {utc_time}")

  db.set_synctime(chan, now)

  utc_time = db.get_synctime(chan)
  print(f"synctime 2: chan: {chan}, utc_time: {utc_time}")
  
  db.insert(chan, msgs, now)

  db.close()

  return 0

def main():
  ret = test0()
  return ret

if __name__ == '__main__':
  os.sys.exit(main())

