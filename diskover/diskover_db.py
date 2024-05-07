#!/usr/bin/env python3
"""
diskover community edition (ce)
https://github.com/diskoverdata/diskover-community/
https://diskoverdata.com

Copyright 2017-2024 Diskover Data, Inc.
"Community" portion of Diskover made available under the Apache 2.0 License found here:
https://www.diskoverdata.com/apache-license/
 
All other content is subject to the Diskover Data, Inc. end user license agreement found at:
https://www.diskoverdata.com/eula-subscriptions/
  
Diskover Data products and features for all versions found here:
https://www.diskoverdata.com/solutions/

"""

import os
import sys
import sqlite3
import json
from distutils.util import strtobool
from config_defaults import config_defaults


def db_connect():
    """Connect to sqlite db and return connection."""
    # Get database file path from config defaults
    dbfile = config_defaults['DATABASE']
    # Check for env var
    if os.getenv('DATABASE') is not None:
        dbfile = os.getenv('DATABASE')

    # Open sqlite database
    try:
        con = sqlite3.connect(dbfile)
    except sqlite3.Error as e:
        print('There was an error connecting to the database! {}'.format(e))
        sys.exit(1)

    # Check database file is writable
    if not os.access(dbfile, os.W_OK):
        print('{} is not writable!'.format(dbfile))
        sys.exit(1)
    
    return con


def db_getconfig():
    """Get config from sqlite db and return config dictionary."""
    con = db_connect()
    cur = con.cursor()
    
    # Set up sqlite configdiskover table if does not yet exist.
    cur.execute("""CREATE TABLE IF NOT EXISTS configdiskover(
    id INTEGER PRIMARY KEY AUTOINCREMENT, 
    name TEXT NOT NULL, 
    value TEXT,
    UNIQUE(name)
    )""")
    con.commit()
    
    config_tups = []
    # Add any missing settings from config_defaults to configdiskover table.
    for name, value in config_defaults.items():
        config_tups.append((name, json.dumps(value)))
    cur.executemany("INSERT OR IGNORE INTO configdiskover ('name', 'value') VALUES(?, ?)", config_tups)
    con.commit()
    
    # Get all config settings from configdiskover table and add to config_dict
    config_dict = {}
    for name, value in cur.execute("SELECT name, value from configdiskover"):
        value = json.loads(value)
        if isinstance(value, str):
            # check if empty string
            if value == "":
                value = None
            # check if bool
            elif value == "true" or value == "false":
                value = bool(strtobool(value))
            # check if int
            elif value.isdigit():
                value = int(value)
            # float
            elif value.isnumeric():
                value = float(value)
        config_dict[name] = value
    
    cur.close()
    con.close()
    
    return config_dict