#!/usr/bin/env python3
"""
diskover
https://diskoverdata.com

Copyright 2017-2021 Diskover Data, Inc.
"Community" portion of Diskover made available under the Apache 2.0 License found here:
https://www.diskoverdata.com/apache-license/
 
All other content is subject to the Diskover Data, Inc. end user license agreement found at:
https://www.diskoverdata.com/eula-subscriptions/
  
Diskover Data products and features for all versions found here:
https://www.diskoverdata.com/solutions/


=== Plugin Name ===
diskover Windows owner/primary group plugin

=== Plugin Description ===
diskover Windows owner plugin - This is an example plugin
for diskover. It updates owner and group fields meta data of 
each file or directory to diskover index during indexing with
the Windows owner and primary group info using pywin32.

=== Plugin Requirements ===
pywin32 python module

=== Diskover Indexing Plugins Requirements ===
all indexing plugins require six functions:
- add_mappings
- add_meta
- add_tags
- for_type
- init
- close

"""

version = '0.0.2'
__version__ = version

import win32security

sid_owner_cache = {}
sid_group_cache = {}


def add_mappings(mappings):
    """Returns a dict with additional es mappings."""
    # return mappings since we are not adding any new index fields
    return mappings


def add_meta(path, osstat):
    """Returns a dict with additional file meta data.
    For any warnings or errors, raise RuntimeWarning or RuntimeError.
    RuntimeWarning and RuntimeError requires two args, error message string and dict or None."""
    # overwrites owner and group default index fields with Windows ownership info.
    return {'owner': get_owner(path), 'group': get_group(path)}


def add_tags(metadict):
    """Returns a dict with additional tag data or return None to not alter tags."""
    return None


def for_type(doc_type):
    """Determine if this plugin should run for file and/or directory."""
    if doc_type in ('file', 'directory'):
        return True
    return False


def init(diskover_globals):
    """Init the plugin.
    Called by diskover when the plugin is first loaded.
    """
    return


def close(diskover_globals):
    """Close the plugin.
    Called by diskover at end of crawl.
    """
    return


def get_owner(filename):
    """This uses the Windows security API
    Get the file's security descriptor, pull out of that the field which refers to the owner and 
    then translate that from the SID to a user name."""
    try:
        sd = win32security.GetFileSecurity(filename, win32security.OWNER_SECURITY_INFORMATION)
        owner_sid = sd.GetSecurityDescriptorOwner()
        owner_sid_str = win32security.ConvertSidToStringSid(owner_sid)
        # check sid cache for owner sid
        if owner_sid_str in sid_owner_cache:
            name, domain, type = sid_owner_cache[owner_sid_str]
        else:
            # lookup sid and cache values
            name, domain, type = win32security.LookupAccountSid(None, owner_sid)
            sid_owner_cache[owner_sid_str] = (name, domain, type)
        owner = domain + '\\' + name
    except Exception as e:
        raise RuntimeWarning('Error getting Windows owner for {0} ({1})'.format(filename, e), None)
    else:
        return owner


def get_group(filename):
    """Like get_owner, but returns primary group."""
    try:
        sd = win32security.GetNamedSecurityInfo(filename, win32security.SE_FILE_OBJECT, 
            win32security.GROUP_SECURITY_INFORMATION)
        primary_group_sid = sd.GetSecurityDescriptorGroup()
        group_sid_str = win32security.ConvertSidToStringSid(primary_group_sid)
        # check sid cache for group sid
        if group_sid_str in sid_group_cache:
            name, domain, type = sid_group_cache[group_sid_str]
        else:
            # lookup sid and cache values
            name, domain, type = win32security.LookupAccountSid(None, primary_group_sid)
            sid_group_cache[group_sid_str] = (name, domain, type)
        group = domain + '\\' + name
    except Exception as e:
        raise RuntimeWarning('Error getting Windows primary group for {0} ({1})'.format(filename, e), None)
    else:
        return group