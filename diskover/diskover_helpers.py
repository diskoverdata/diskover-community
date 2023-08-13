#!/usr/bin/env python3
"""
diskover community edition (ce)
https://github.com/diskoverdata/diskover-community/
https://diskoverdata.com

Copyright 2017-2023 Diskover Data, Inc.
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
import warnings
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
config_filename = os.path.join(config.config_dir(), confuse.CONFIG_FILENAME)
if not os.path.exists(config_filename):
    print('Config file {0} not found! Copy from default config.'.format(config_filename))
    sys.exit(1)
    
# load default config file
config_defaults = confuse.Configuration('diskover', __name__)
scriptpath = os.path.dirname(os.path.realpath(__file__))
defaultconfig_filename = os.path.join(scriptpath, 'configs_sample/diskover/config.yaml')
config_defaults.set_file(defaultconfig_filename)

def config_warn(e):
    warnings.warn('Config setting {}. Using default.'.format(e))

# laod config values
try:
    exc_dirs = config['diskover']['excludes']['dirs'].get()
except confuse.NotFoundError as e:
    config_warn(e)
    exc_dirs = config_defaults['diskover']['excludes']['dirs'].get()
try:
    exc_files = config['diskover']['excludes']['files'].get()
except confuse.NotFoundError as e:
    config_warn(e)
    exc_files = config_defaults['diskover']['excludes']['files'].get()
try:
    inc_dirs = config['diskover']['includes']['dirs'].get()
except confuse.NotFoundError as e:
    config_warn(e)
    inc_dirs = config_defaults['diskover']['includes']['dirs'].get()
try:
    inc_files = config['diskover']['includes']['files'].get()
except confuse.NotFoundError as e:
    config_warn(e)
    inc_files = config_defaults['diskover']['includes']['files'].get()
try:
    og_uidgidonly = config['diskover']['ownersgroups']['uidgidonly'].get()
except confuse.NotFoundError as e:
    config_warn(e)
    og_uidgidonly = config_defaults['diskover']['ownersgroups']['uidgidonly'].get()
try:
    og_domain = config['diskover']['ownersgroups']['domain'].get()
except confuse.NotFoundError as e:
    config_warn(e)
    og_domain = config_defaults['diskover']['ownersgroups']['domain'].get()
try:
    og_domainsep = config['diskover']['ownersgroups']['domainsep'].get()
except confuse.NotFoundError as e:
    config_warn(e)
    og_domainsep = config_defaults['diskover']['ownersgroups']['domainsep'].get()
try:
    og_domainfirst = config['diskover']['ownersgroups']['domainfirst'].get()
except confuse.NotFoundError as e:
    config_warn(e)
    og_domainfirst = config_defaults['diskover']['ownersgroups']['domainfirst'].get()
try:
    og_keepdomain = config['diskover']['ownersgroups']['keepdomain'].get()
except confuse.NotFoundError as e:
    config_warn(e)
    og_keepdomain = config_defaults['diskover']['ownersgroups']['keepdomain'].get()
try:
    replacepaths = config['diskover']['replacepaths']['replace'].get()
except confuse.NotFoundError as e:
    config_warn(e)
    replacepaths = config_defaults['diskover']['replacepaths']['replace'].get()
finally:
    if IS_WIN:
        replacepaths = True
try:
    replacepaths_from = config['diskover']['replacepaths']['from'].get()
except confuse.NotFoundError as e:
    config_warn(e)
    replacepaths_from = config_defaults['diskover']['replacepaths']['from'].get()
try:
    replacepaths_to = config['diskover']['replacepaths']['to'].get()
except confuse.NotFoundError as e:
    config_warn(e)
    replacepaths_to = config_defaults['diskover']['replacepaths']['to'].get()
try:
    plugins_enabled = config['diskover']['plugins']['enable'].get()
except confuse.NotFoundError as e:
    config_warn(e)
    plugins_enabled = config_defaults['diskover']['plugins']['enable'].get()
try:
    plugins_dirs = config['diskover']['plugins']['dirs'].get()
except confuse.NotFoundError as e:
    config_warn(e)
    plugins_dirs = config_defaults['diskover']['plugins']['dirs'].get()
try:
    plugins_files = config['diskover']['plugins']['files'].get()
except confuse.NotFoundError as e:
    config_warn(e)
    plugins_files = config_defaults['diskover']['plugins']['files'].get()
    

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
    for d in exc_dirs:
        if d == '.*':
            continue
        
        if d.startswith('*'):
            d = d.lstrip('*')
            
        if d.endswith('/'):
            d = d.rstrip('/')
        
        try:
            res = re.search(d, name)
        except re.error as e:
            raise Exception(e)
        else:
            if res:
                return True
            
        try:
            res = re.search(d, path)
        except re.error as e:
            raise Exception(e)
        else:
            if res:
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
                owner = pwd.getpwuid(uid).pw_name
                # check if domain in name and if it should be removed
                if og_domain and not og_keepdomain and og_domainsep in owner:
                    if og_domainfirst:
                        owner = owner.split(og_domainsep)[1]
                    else:
                        owner = owner.split(og_domainsep)[0]
            except Exception:
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
                group = grp.getgrgid(gid).gr_name
                # check if domain in name and if it should be removed
                if og_domain and not og_keepdomain and og_domainsep in group:
                    if og_domainfirst:
                        group = group.split(og_domainsep)[1]
                    else:
                        group = group.split(og_domainsep)[0]
            except Exception:
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
        # Check if too large for long field mapping used by total
        maxlongint = 9007199254740992  # 8 PB
        if total > maxlongint:
            total = maxlongint
        if free > maxlongint:
            free = maxlongint
        if available > maxlongint:
            available = maxlongint
        data = {
            'path': mount_path,
            'total': total,
            'used': total - free,
            'free': free,
            'free_percent': round((total-(total-free))/total*100, 6),
            'available': available,
            'available_percent': round((total-(total-available))/total*100, 6),
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
            # Check if too large for long field mapping used by total
            maxlongint = 9007199254740992  # 8 PB
            if total > maxlongint:
                total = maxlongint
            if free > maxlongint:
                free = maxlongint
            if available > maxlongint:
                available = maxlongint
            data = {
                'path': mount_path,
                'total': total,
                'used': total - free,
                'free': free,
                'free_percent': round((total-(total-free))/total*100, 6),
                'available': available,
                'available_percent': round((total-(total-available))/total*100, 6),
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
        path = rem_win_path(path)
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
        path = path.rstrip('/')
    if replacepaths_from and replacepaths_to:
        path = path.replace(replacepaths_from, replacepaths_to, 1)
        path = path.rstrip('/')
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


def handle_unicode(f, ignore_errors=False):
    """Check file path can be encoded to utf-8 since this breaks bulk index uploads.
    """
    if ignore_errors:
        err = 'replace'
    else:
        err = 'strict'
    try:
        # try to encode utf-8
        return f.encode('utf-8', errors=err).decode('utf-8')
    except UnicodeEncodeError:
        raise UnicodeError


def get_file_name(file, ignore_errors=False):
    return handle_unicode(file, ignore_errors=ignore_errors)


def get_dir_name(path, ignore_errors=False):
    if replacepaths:
        path = replace_path(path)
    path = os.path.basename(path)
    return handle_unicode(path, ignore_errors=ignore_errors)


def get_parent_path(path, ignore_errors=False):
    if replacepaths:
        path = replace_path(path)
    path = os.path.dirname(path)
    return handle_unicode(path, ignore_errors=ignore_errors)


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
    

def get_win_path(path):
    """Returns a Windows extended device path to bypass normalization.
    Fixes Windows long paths and other path related issues such as trailing space."""
    if path[:1] == '\\':
        return '\\\\?\\UNC' + path[1:]
    else:
        return '\\\\?\\' + path


def rem_win_path(path):
    """Removes Windows extended device path from path."""
    if '\\\\?\\UNC\\' in path:
        return path.replace('\\\\?\\UNC', '\\')
    else:
        return path.replace('\\\\?\\', '')
