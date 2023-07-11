import sqlite3
import subprocess
import os
import time
import re

import urllib.parse

from shutil import copyfile

backlinks_header = '\n\n---\n### Backlinks'
possible_backlinks_headers = ['### Backlinks', '## Backlinks']
add_unreferenced_links_search_link = True
HOME = os.getenv('HOME', '')
bear_db = os.path.join(HOME, 'Library/Group Containers/9K33E3U3T4.net.shinyfrog.bear/Application Data/database.sqlite')

from datetime import datetime
import re


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

def x_callback(x_command, md_text):
    x_command_text = x_command + '&text=' + urllib.parse.quote(md_text.encode('utf8'))
    subprocess.call(["open", "-g", x_command_text])
    time.sleep(.2)


def update_note(uid, new_text):
    x_command = 'bear://x-callback-url/add-text?id=' + uid +'&mode=replace_all&open_note=no&exclude_trashed=no&new_window=no&show_window=no&edit=no&timestamp=no'
    x_callback(x_command, new_text)


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

    import re

    possible_backlinks_headers = [
        '---\n### Backlinks',
        # '## Backlinks'
    ]
    # pattern = r"(^#+\s.*$)"
    pattern = r"(^(---\n)?#+\s.*$)"  # The (\n\n---\n)? part is an optional non-capturing group


    # Loop over the notes:
    for counter, note in enumerate(notes):
        # Split Note text from backlinks
        note_text = note['Text']

        # Find all header matches
        header_matches = [[match.group(), match.start(), match.end()] for match
                          in re.finditer(pattern, note_text, re.M)]

        new_note_text = ""
        last_end = 0

        header_removed = False

        # Now compose the new note text, by removing all backlinks headers and all text following them (until the next header, if any).
        for header, start, end in header_matches:
            # If the header is a backlinks header
            if header.rstrip() in possible_backlinks_headers:
                # If this is not the last header in the note, exit the loop without doing any changes
                # FIXME: this is done because some note have text inside the backlinks section that would be deleted!
                if header_matches.index([header, start, end]) + 1 < len(header_matches):
                    break

                header_removed = True
                new_note_text += note_text[
                                 last_end:start]  # Keep the text before the header
                # Find the next header's start (or the end of the note if there is no next header)
                next_start = \
                header_matches[header_matches.index([header, start, end]) + 1][
                    1] if header_matches.index([header, start, end]) + 1 < len(
                    header_matches) else len(note_text)
                last_end = next_start  # Skip the text after the header until the next header
            else:  # If the header is not a backlinks header
                new_note_text += note_text[
                                 last_end:end + 1]  # Keep the text before and including the header
                last_end = end + 1


        if header_removed:
            # Add the remaining text after the last header (or all of it if there was no header)
            new_note_text += note_text[last_end:]

            # #  Print old and new note text
            # if header_removed:
            #     print("################# Old note text: {}".format(note_text))
            #     print("################# New note text: {}".format(new_note_text))
            #     print("\n\n\n\n")

            print(f"Updating note {note['Title']} ")
            print("")
            update_note(note['UID'], new_note_text)
            # print(new_note_text)

    print("Done")



if __name__ == '__main__':
    main()
