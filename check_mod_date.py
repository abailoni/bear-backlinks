'''
# Bear backlinks
# Inspired by https://github.com/DeLub/bear-backlinks

This script loops through all notes in your bear database and checks which
other notes reference it. The notes referencing this note are listed under
`## Backlinks`. Each run replaces all backlinks already present in the note.

I believe looping through all notes is necessary to account for links that have
been removed. I have not tested how well this works on large collections of
notes.

This script does not update the notes directly in the database. It only reads
the notes and the links from your database, and uses Bear's x-callback-url to
update the note text.

Change the `backlinks_header` to the name of the section you want to use.

This script can be used with the standard Python 2.7 on macOS.
'''
import sqlite3
import subprocess
import os
import time
import json
import numpy as np
import h5py
import re

import urllib.parse

from shutil import copyfile

backlinks_header = '\n\n---\n### Backlinks'
HOME = os.getenv('HOME', '')
bear_db = os.path.join(HOME, 'Library/Group Containers/9K33E3U3T4.net.shinyfrog.bear/Application Data/database.sqlite')
# bear_db = './databases/BAK.sqlite'
old_mod_dates_file = './databases/mod_dates.h5'

from datetime import datetime


def main():
    # Read database again and save mod-dates to array for next run:
    notes = get_all_notes()
    for counter, note in enumerate(notes):
        if counter == 0:
            max_nb_notes = note['ID'] + 1
            new_modification_dates = np.empty(max_nb_notes, dtype='float64')
        new_modification_dates[note['ID']] = note['ModDate']

    with h5py.File(old_mod_dates_file, 'w') as f:
        f['data'] = new_modification_dates
    print("Done")


def get_all_notes():
    "Get notes ordered by ID (decreasing)"
    with sqlite3.connect(bear_db) as conn:
        conn.row_factory = sqlite3.Row
        query = "SELECT TNote.Z_PK              AS ID\
                      , TNote.ZUNIQUEIDENTIFIER AS UID\
                      , TNote.ZTITLE            AS Title\
                      , TNote.ZTEXT             AS Text\
                      , TNote.ZMODIFICATIONDATE AS ModDate\
                   FROM ZSFNOTE                 AS TNote\
                  WHERE TNote.ZTRASHED = 0\
               ORDER BY TNote.Z_PK DESC"
        return conn.execute(query)

def get_notes_linking_to(id):
    with sqlite3.connect(bear_db) as conn:
        conn.row_factory = sqlite3.Row
        query = "SELECT DISTINCT\
                        SNote.Z_PK              AS ID\
                      , SNote.ZUNIQUEIDENTIFIER AS UID\
                      , SNote.ZTITLE            AS Title\
                      , SNote.ZTEXT             AS Text\
                   FROM Z_7LINKEDNOTES          AS Source\
                      , ZSFNOTE                 AS SNote\
                  WHERE Source.Z_7LINKEDNOTES = %i\
                    AND SNote.Z_PK            = Source.Z_7LINKEDBYNOTES\
                    AND SNote.ZTRASHED        = 0\
               ORDER BY SNote.ZMODIFICATIONDATE ASC" % id
        return conn.execute(query)

def get_note_links_in(id):
    with sqlite3.connect(bear_db) as conn:
        conn.row_factory = sqlite3.Row
        query = "SELECT DISTINCT\
                        SNote.Z_PK              AS ID\
                   FROM Z_7LINKEDNOTES          AS Source\
                      , ZSFNOTE                 AS SNote\
                  WHERE Source.Z_7LINKEDBYNOTES = %i\
                    AND SNote.Z_PK            = Source.Z_7LINKEDNOTES\
                    AND SNote.ZTRASHED        = 0\
               ORDER BY SNote.ZCREATIONDATE ASC" % id
        return conn.execute(query)

def update_note(uid, new_text):
    x_command = 'bear://x-callback-url/add-text?id=' + uid +'&mode=replace_all&open_note=no&exclude_trashed=no&new_window=no&show_window=no&edit=no&timestamp=no'
    x_callback(x_command, new_text)

def x_callback(x_command, md_text):
    x_command_text = x_command + '&text=' + urllib.parse.quote(md_text.encode('utf8'))
    subprocess.call(["open", "-g", x_command_text])
    time.sleep(.2)

if __name__ == '__main__':
    main()
