#!/usr/bin/env python3
"""
diskover community edition (ce)
https://github.com/diskoverdata/diskover-community/
https://diskoverdata.com

Copyright 2017-2021 Diskover Data, Inc.
"Community" portion of Diskover made available under the Apache 2.0 License found here:
https://www.diskoverdata.com/apache-license/
 
All other content is subject to the Diskover Data, Inc. end user license agreement found at:
https://www.diskoverdata.com/eula-subscriptions/
  
Diskover Data products and features for all versions found here:
https://www.diskoverdata.com/solutions/

"""

import os
import sys
import confuse
import re
import math
import importlib
from datetime import datetime, timezone
from threading import Lock
if os.name == 'nt':
    try:
        import psutil
    except ModuleNotFoundError:
        print('Windows requires psutil Python module')
        sys.exit(1)
    from os.path import splitdrive
    IS_WIN = True
else:
    import pwd
    import grp
    from resource import getrusage, RUSAGE_SELF
    IS_WIN = False

"""Load yaml config file."""
config = confuse.Configuration('diskover', __name__)

try:
    exc_dirs = config['diskover']['excludes']['dirs'].get()
    exc_files = config['diskover']['excludes']['files'].get()
    inc_dirs = config['diskover']['includes']['dirs'].get()
    inc_files = config['diskover']['includes']['files'].get()
    og_uidgidonly = config['diskover']['ownersgroups']['uidgidonly'].get()
    og_domain = config['diskover']['ownersgroups']['domain'].get()
    og_domainsep = config['diskover']['ownersgroups']['domainsep'].get()
    og_domainfirst = config['diskover']['ownersgroups']['domainfirst'].get()
    og_keepdomain = config['diskover']['ownersgroups']['keepdomain'].get()
    replacepaths = config['diskover']['replacepaths']['replace'].get()
    if IS_WIN:
        replacepaths = True
    replacepaths_from = config['diskover']['replacepaths']['from'].get()
    replacepaths_to = config['diskover']['replacepaths']['to'].get()
    plugins_enabled = config['diskover']['plugins']['enable'].get()
    plugins_dirs = config['diskover']['plugins']['dirs'].get()
    plugins_files = config['diskover']['plugins']['files'].get()
    es_timeout = config['databases']['elasticsearch']['timeout'].get()
except confuse.NotFoundError as e:
    print('Config ERROR: {0}, check config for errors or missing settings from default config.'.format(e))
    sys.exit(1)

uids_owners = {}
gids_groups = {}
uidgid_lock = Lock()


def dir_excluded(path):
    """Return True if path in exc_dirs, False if not in the list."""
    # return False if dir exclude list is empty
    if not exc_dirs:
        return False
    name = os.path.basename(path)
    # return if directory in included list (whitelist)
    if name in inc_dirs or path in inc_dirs:
        return False
    # skip any dirs in exc_dirs
    if name in exc_dirs or path in exc_dirs:
        return True
    # skip any dirs which start with . (dot) and in exc_dirs
    if name.startswith('.') and u'.*' in exc_dirs:
        return True
    # skip any dirs that are found in reg exp checks including wildcard searches
    found_dir = False
    found_path = False
    for d in exc_dirs:
        if d == '.*':
            continue
        if d.startswith('*') and d.endswith('*'):
            d = d.replace('*', '')
            if re.search(d, name):
                found_dir = True
                break
            elif re.search(d, path):
                found_path = True
                break
        elif d.startswith('*'):
            d = d + '$'
            if re.search(d, name):
                found_dir = True
                break
            elif re.search(d, path):
                found_path = True
                break
        elif d.endswith('*'):
            d = '^' + d
            if re.search(d, name):
                found_dir = True
                break
            elif re.search(d, path):
                found_path = True
                break
        else:
            if d.rstrip('/') == name:
                found_dir = True
                break
            elif d.rstrip('/') == path:
                found_path = True
                break
    if found_dir or found_path:
        return True
    return False


def file_excluded(filename):
    """Return True if path or ext in exc_files, False if not in the list."""
    # return False if file exclude list is empty
    if not exc_files:
        return False
    # return if filename in included list (whitelist)
    if filename in inc_files:
        return False
    # check for filename in excluded_files set
    if filename in exc_files:
        return True
    # check for extension in and . (dot) files in excluded_files
    extension = os.path.splitext(filename)[1][1:].lower()
    if (not extension and 'NULLEXT' in exc_files) or \
        '*.' + extension in exc_files or \
            (filename.startswith('.') and u'.*' in exc_files):
        return True
    return False


def get_time(seconds):
    """Returns human readable time format for stats."""
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)
    return "%dd:%dh:%02dm:%02ds" % (d, h, m, s)


def convert_size(size_bytes):
    """Returns human readable file sizes."""
    if size_bytes == 0:
        return '0 B'
    size_name = ('B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB')
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return '{0} {1}'.format(s, size_name[i])


def get_owner_group_names(uid, gid):
    """Get owner and group names and deals with uid/gid -> name cacheing."""
    global uids_owners
    global gids_groups

    # try to get owner user name
    # first check cache
    owner = None
    if uid in uids_owners:
        owner = uids_owners[uid]
    # not in cache
    if owner is None:
        # check if we should just get uid or try to get owner name
        if og_uidgidonly:
            owner = uid
        else:
            try:
                # check if domain in name
                if og_domain:
                    # check if we should remove the domain from owner
                    if og_keepdomain:
                        owner = pwd.getpwuid(uid).pw_name
                    else:
                        if og_domainfirst:
                            owner = pwd.getpwuid(uid).pw_name.split(og_domainsep)[1]
                        else:
                            owner = pwd.getpwuid(uid).pw_name.split(og_domainsep)[0]
                else:
                    owner = pwd.getpwuid(uid).pw_name
            # if we can't find the owner's user name, use the uid number
            except KeyError:
                owner = uid
        with uidgid_lock:
            # store it in cache
            uids_owners[uid] = owner

    # try to get group name
    # first check cache
    group = None
    if gid in gids_groups:
        group = gids_groups[gid]
    # not in cache
    if group is None:
        # check if we should just get gid or try to get group name
        if og_uidgidonly:
            group = gid
        else:
            try:
                # check if domain in name
                if og_domain:
                    # check if we should remove the domain from group
                    if og_keepdomain:
                        group = grp.getgrgid(gid).gr_name
                    else:
                        if og_domainfirst:
                            group = grp.getgrgid(gid).gr_name.split(og_domainsep)[1]
                        else:
                            group = grp.getgrgid(gid).gr_name.split(og_domainsep)[0]
                else:
                    group = grp.getgrgid(gid).gr_name
            # if we can't find the group's name, use the gid number
            except KeyError:
                group = gid
        with uidgid_lock:
            # store in cache
            gids_groups[gid] = group

    return owner, group


def index_info_crawlstart(es, index, path, start, ver, altscanner):
    """Index total, used, free and available disk space and some 
    index info like path, etc. Index all different mount points under 
    top path, example multiple storage servers mounted under /mnt."""
    
    # check for alternate scanner
    if altscanner is not None:
        total, free, available = altscanner.get_storage_size(path)
        mount_path = path
        if replacepaths:
            mount_path = replace_path(mount_path)
        data = {
            'path': mount_path,
            'total': total,
            'used': total - free,
            'free': free,
            'available': available,
            'type': 'spaceinfo'
        }
        es.index(index=index, body=data)
    else:
        mounts = []
        mounts.append(path)
        for entry in os.scandir(path):
            if entry.is_symlink():
                pass
            elif entry.is_dir():
                if not dir_excluded(entry.path):
                    if os.path.ismount(entry.path):
                        mounts.append(entry.path)
        for mount_path in mounts:
            if not IS_WIN:
                statvfs = os.statvfs(mount_path)
                # Size of filesystem in bytes
                total = statvfs.f_frsize * statvfs.f_blocks
                # Actual number of free bytes
                free = statvfs.f_frsize * statvfs.f_bfree
                # Number of free bytes that ordinary users are allowed
                # to use (excl. reserved space)
                available = statvfs.f_frsize * statvfs.f_bavail
            else:
                import ctypes
                total_bytes = ctypes.c_ulonglong(0)
                free_bytes = ctypes.c_ulonglong(0)
                available_bytes = ctypes.c_ulonglong(0)
                ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(mount_path),
                    ctypes.pointer(available_bytes),
                    ctypes.pointer(total_bytes),
                    ctypes.pointer(free_bytes))
                total = total_bytes.value
                free = free_bytes.value
                available = available_bytes.value
            if replacepaths:
                mount_path = replace_path(mount_path)
            data = {
                'path': mount_path,
                'total': total,
                'used': total - free,
                'free': free,
                'available': available,
                'type': 'spaceinfo'
            }
            es.index(index=index, body=data)
    if replacepaths:
        path = replace_path(path)
    data = {
            'path': path,
            'start_at': start,
            'diskover_ver': ver,
            'type': 'indexinfo'
        }
    es.index(index=index, body=data)


def index_info_crawlend(es, index, path, size, size_du, filecount, dircount, end, elapsed):
    """Index some index info like total size, du size, file counts, etc."""
    if replacepaths:
        path = replace_path(path)
    data = {
        'path': path,
        'file_size': size,
        'file_size_du': size_du,
        'file_count': filecount,
        'dir_count': dircount,
        'end_at': end,
        'crawl_time': elapsed,
        'type': 'indexinfo'
    }
    es.index(index=index, body=data)


def replace_path(path):
    """Replace paths and drive letters."""
    if IS_WIN:
        d, p = os.path.splitdrive(path)
        # change any drive letter, example from P:\ to /P_drive
        if re.search('^[a-zA-Z]:', path) is not None:
            if p == '\\': p = ''
            path = '/' + d.rstrip(':').upper() + '_drive' + p
        # change any unc paths, example \\stor1\share to /stor1/share
        elif re.search('^\\\\', path) is not None:
            path = '/' + d.lstrip('\\') + p
        # change any windows path separator \ to /
        path = path.replace('\\', '/')
    if replacepaths_from and replacepaths_to:
        path = path.replace(replacepaths_from, replacepaths_to, 1)
    return path


def escape_chars(text):
    """This is the escape special characters function.
    It returns escaped path strings for es queries.
    """
    # escape any backslash chars
    text = text.replace('\\', '\\\\')
    # escape any characters in chr_dict
    chr_dict = {'\n': '\\n', '\t': '\\t',
                '/': '\\/', '(': '\\(', ')': '\\)', '[': '\\[', ']': '\\]', '$': '\\$',
                ' ': '\\ ', '&': '\\&', '<': '\\<', '>': '\\>', '+': '\\+', '-': '\\-',
                '|': '\\|', '!': '\\!', '{': '\\{', '}': '\\}', '^': '\\^', '~': '\\~',
                '?': '\\?', ':': '\\:', '=': '\\=', '\'': '\\\'', '"': '\\"', '@': '\\@',
                '.': '\\.', '#': '\\#', '*': '\\*', '　': '\\　'}
    text_esc = text.translate(str.maketrans(chr_dict))
    return text_esc


def handle_unicode(f):
    try:
        return f.encode('utf-8').decode('utf-8')
    except UnicodeEncodeError:
        raise UnicodeError


def get_file_name(file):
    return handle_unicode(file)


def get_dir_name(path):
    if replacepaths:
        path = replace_path(path)
    path = os.path.basename(path)
    return handle_unicode(path)


def get_parent_path(path):
    if replacepaths:
        path = replace_path(path)
    path = os.path.dirname(path)
    return handle_unicode(path)


def isoutc_to_timestamp(utctime):
    """Convert iso utc time to unix timestamp."""
    return int(datetime.strptime(utctime, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc).timestamp())


def timestamp_to_isoutc(timestamp):
    """Convert unix timestamp to iso utc time."""
    return datetime.utcfromtimestamp(int(timestamp)).isoformat()


def get_plugins_info():
    """This is the get plugins info function.
    It gets a list of python plugins info (modules) in
    the plugins directory and returns the plugins information.
    """
    plugin_dir = os.path.join(os.path.dirname(__file__), 'plugins')
    # check if plugin directory exists, if not create it
    if not os.path.exists(plugin_dir):
        os.mkdir(plugin_dir)
    main_module = '__init__'
    plugins_info = []
    possible_plugins = os.listdir(plugin_dir)
    for i in possible_plugins:
        location = os.path.join(plugin_dir, i)
        if not os.path.isdir(location) or not main_module + '.py' \
                in os.listdir(location):
            continue
        # check if plugin is enabled
        if i in plugins_files or i in plugins_dirs:
            spec = importlib.machinery.PathFinder().find_spec(main_module, [location])
            plugins_info.append({'name': i, 'spec': spec})
    return plugins_info


def load_plugins():
    """This is the load plugins function.
    It dynamically load the plugins and return them in a list
    """
    loaded_plugins = []
    if not plugins_enabled:
        return loaded_plugins
    plugins_info = get_plugins_info()
    for plugin_info in plugins_info:
        plugin_module = importlib.util.module_from_spec(plugin_info['spec'])
        plugin_info['spec'].loader.exec_module(plugin_module)
        loaded_plugins.append(plugin_module)
    return loaded_plugins


def plugins_init(plugins):
    """Initialize plugins.
    """
    if not plugins:
        return
    for plugin in plugins:
        res = plugin.init()
        if res is not True:
            print('{0} plugin init error: {1}'.format(plugin['name']), res)
            sys.exit(1)
            

def plugins_close(plugins):
    """Close plugins.
    """
    if not plugins:
        return
    for plugin in plugins:
        res = plugin.stop()
        if res is not True:
            print('{0} plugin close error: {1}'.format(plugin['name']), res)
            

def list_plugins():
    """This is the list plugins function.
    It prints the name of all the available plugins
    """
    if not plugins_enabled:
        print('Plugins disabled in config')
    else:
        plugins_info = get_plugins_info()
        if not plugins_info:
            print('No plugins found')
        else:
            dirplugs = []
            fileplugs = []
            for plugin_info in plugins_info:
                if plugin_info['name'] in plugins_dirs:
                    dirplugs.append(plugin_info['name'])
                if plugin_info['name'] in plugins_files:
                    fileplugs.append(plugin_info['name'])
            print('file:')
            print(fileplugs)
            print('directory:')
            print(dirplugs)


def set_times(path, atime, mtime):
    """Sets access/ modified times for files."""
    try:
        os.utime(path, (atime, mtime))
    except OSError as e:
        return False, e
    return True, None


def get_mem_usage():
    """Gets the RUSAGE memory usage, returns in human readable format GB, MB, KB, etc.
    """
    if IS_WIN:
        process = psutil.Process(os.getpid())
        return convert_size(process.memory_info().rss) # in bytes 
    mem = getrusage(RUSAGE_SELF).ru_maxrss
    if sys.platform == 'darwin':
        # macos
        return convert_size(mem) # in bytes
    else:
        # linux
        return convert_size(mem * 1024) # convert kb to bytes