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

This script can be used with the standard Python 3.7 on macOS.
'''
import sqlite3
import subprocess
import os
import time
import re

import urllib.parse

from shutil import copyfile

backlinks_header = '\n\n---\n### Backlinks'
HOME = os.getenv('HOME', '')
bear_db = os.path.join(HOME, 'Library/Group Containers/9K33E3U3T4.net.shinyfrog.bear/Application Data/database.sqlite')

from datetime import datetime


def main():
    # current date and time
    # TODO: delete some of the old backups?
    now = datetime.now()
    dt_string = now.strftime("%d-%m-%Y-%H-%M-%S")
    BAK_db = bear_db.replace(".sqlite", "_{}.sqlite".format(dt_string))
    copyfile(bear_db, BAK_db)

    tick = time.time()
    notes = get_all_notes()
    print("Read in ", time.time() - tick)
    # max_nb_notes = len(notes) + 1000

    # Loop over the notes:
    for counter, note in enumerate(notes):
        # Split Note text from backlinks
        split_note = note['Text'].split(backlinks_header)
        note_text = split_note[0]

        # Get list of current backlinks:
        nb_found_backlinks = 0
        if len(split_note) == 1:
            old_backlinks = []
        elif len(split_note) == 2:
            old_backlinks = get_current_backlinks(split_note[1])
        else:
            raise ValueError("Something went wrong while detecting backlinks in note: {}".format(note["Title"]))

        backlinks = backlinks_header

        # Get notes this note is referenced by
        linked_by_notes = get_notes_linking_to(note['ID'])

        # Make sure that we also match sub-links:
        re_note_title = re.compile(r"\[\[(" + re.escape(note['Title']) + r")(|.+)\]\]")

        update_backlinks = False
        for linked_by_note in linked_by_notes:
            lb_note_text = linked_by_note['Text'].split(backlinks_header)[0]
            # Only add if link is in the text and if it is not already linked
            if re_note_title.search(lb_note_text) is not None:
                re_lb_note_title = re.compile(r"\[\[(" + re.escape(linked_by_note['Title']) + r")(|.+)\]\]")
                if re_lb_note_title.search(note_text) is None:
                    # Check if backlink was already there:
                    # We will update the note only if at least one is different
                    # (They will even be updated when their order change)
                    if len(old_backlinks) <= nb_found_backlinks:
                        update_backlinks = True
                    elif old_backlinks[nb_found_backlinks] != linked_by_note['Title']:
                        update_backlinks = True

                    # Add to current backlink list:
                    backlinks += "\n- [[" + linked_by_note['Title'] + "]]"
                    nb_found_backlinks += 1

        # Check if we found some new ones:
        if nb_found_backlinks != len(old_backlinks):
            update_backlinks = True

        if update_backlinks:
            print("Backlinks updated in note: {}".format(note['Title']))
            # If we did not found any link, remove the Backlinks section:
            if nb_found_backlinks > 0:
                note_text += backlinks
            update_note(note['UID'], note_text)

    print("Done")


def get_current_backlinks(backlinks_text):
    re_links = re.compile(r"\[\[.+\]\]")
    # Find all links:
    matches = re_links.findall(backlinks_text)
    # Remove brackets and return:
    return [match.replace('[[', '').replace(']]', '') for match in matches]


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
                      , SNote.ZMODIFICATIONDATE AS ModDate\
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
