#!/usr/bin/env python3
"""
diskover community edition (ce)
https://github.com/diskoverdata/diskover-community/
https://diskoverdata.com

Copyright 2017-2022 Diskover Data, Inc.
"Community" portion of Diskover made available under the Apache 2.0 License found here:
https://www.diskoverdata.com/apache-license/

All other content is subject to the Diskover Data, Inc. end user license agreement found at:
https://www.diskoverdata.com/eula-subscriptions/

Diskover Data products and features for all versions found here:
https://www.diskoverdata.com/solutions/

"""

import os
import logging
import confuse
import warnings
import ftplib
import ssl
from os.path import join
from threading import Lock

import ftputil
import ftputil.session


__version__ = '0.0.1'

class ConfigurationError(Exception): pass


def init(diskover_globals):
    # Load yaml config file
    config = confuse.Configuration('diskover_scandir_ftp', __name__)
    config_filename = os.path.join(config.config_dir(), confuse.CONFIG_FILENAME)
    if not os.path.exists(config_filename):
        print('Config file {0} not found! Copy from default config.'.format(config_filename))
        raise SystemExit(1)

    # load default config file
    config_defaults = confuse.Configuration('diskover_scandir_ftp', __name__)
    scriptpath = os.path.dirname(os.path.realpath(__file__))
    scriptparentpath = os.path.dirname(scriptpath)
    defaultconfig_filename = os.path.join(scriptparentpath, 'configs_sample/diskover_scandir_ftp/config.yaml')
    config_defaults.set_file(defaultconfig_filename)

    def config_warn(e):
        warnings.warn('Config setting {}. Using default.'.format(e))

    try:
        user = config['user'].get()
    except confuse.NotFoundError as e:
        config_warn(e)
        user = config_defaults['user'].get()

    try:
        password = config['password'].get()
    except confuse.NotFoundError as e:
        config_warn(e)
        password = config_defaults['password'].get()

    try:
        host = config['host'].get()
    except confuse.NotFoundError as e:
        config_warn(e)
        host = config_defaults['host'].get()

    try:
        port = config['port'].get()
    except confuse.NotFoundError as e:
        config_warn(e)
        port = config_defaults['port'].get()

    try:
        active = config['active'].get()
    except confuse.NotFoundError as e:
        config_warn(e)
        active = config_defaults['active'].get()

    try:
        ftp_over_tls = config['ftp_over_tls'].get()
    except confuse.NotFoundError as e:
        config_warn(e)
        ftp_over_tls = config_defaults['ftp_over_tls'].get()

    try:
        storage_size = config['storage_size'].get()
    except confuse.NotFoundError as e:
        config_warn(e)
        storage_size = config_defaults['storage_size'].get()

    try:
        debug = config['debug'].get()
    except confuse.NotFoundError as e:
        config_warn(e)
        debug = config_defaults['debug'].get()

    # print config being used
    ftplogger.info('Config file: {0}'.format(config_filename))

    # ftpserver is instantiated globally at import
    ftpserver.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        active=active,
        ftp_over_tls=ftp_over_tls,
        storage_size=storage_size,
        debug=debug
    )


def log_setup(loglevel, logformat, filelogging, handler_file, handler_warnfile, handler_con):
    global ftplogger
    global ftplogger_warn
    global logtofile
    if filelogging:
        logtofile = True
    else:
        logtofile = False
    ftplogger = logging.getLogger('scandir_ftp')
    ftplogger_warn = logging.getLogger('scandir_ftp_warn')
    ftplogger.setLevel(loglevel)
    if logtofile:
        ftplogger.addHandler(handler_file)
        ftplogger.addHandler(handler_con)
        ftplogger_warn.addHandler(handler_warnfile)
        ftplogger.setLevel(loglevel)
    else:
        logging.basicConfig(format=logformat, level=loglevel)


class stat_result(object):
    __slots__ = ('st_mode', 'st_ino', 'st_dev', 'st_nlink', 'st_uid', 'st_gid', 'st_size',
                 'st_atime', 'st_mtime', 'st_ctime', 'st_sizedu')

    def __init__(self, stat_tup):
        perms, st_uid, st_gid, st_size, st_mtime = stat_tup
        # standard stat params
        self.st_mode = perms
        self.st_ino = None
        self.st_dev = None
        self.st_nlink = 0
        self.st_uid = st_uid
        self.st_gid = st_gid
        self.st_size = st_size
        self.st_atime = st_mtime
        self.st_mtime = st_mtime
        self.st_ctime = st_mtime
        # size used (allocated) param
        self.st_sizedu = st_size

    def __repr__(self):
        return f'<{self.__class__.__name__}: mode: {self.st_mode} uid: ' \
               f'{self.st_uid} gid: {self.st_gid} size: {self.st_size} mtime: {self.st_mtime}>'


class FTPDirEntry:
    __slots__ = ('name', '_scandir_path', '_path', '_server')

    def __init__(self, scandir_path, name, server):
        self._scandir_path = scandir_path
        self.name = name
        self._server = server
        self._path = None

    @property
    def path(self):
        if self._path is None:
            self._path = join(self._scandir_path, self.name)
        return self._path

    def stat(self):
        return self._server.stat(self.path)

    def is_dir(self):
        with self._server.lock:
            return self._server.ftp_host.path.isdir(self.path)

    def is_file(self):
        with self._server.lock:
            return self._server.ftp_host.path.isfile(self.path)

    def is_symlink(self):
        with self._server.lock:
            return self._server.ftp_host.path.islink(self.path)

    def inode(self):
        return None

    def __str__(self):
        return '<{0}: {1!r}>'.format(self.__class__.__name__, self.name)

    __repr__ = __str__


class FTPServer:
    def __init__(self):
        self.host = None
        self.port = None
        self.user = None
        self.password = None
        self.active = None
        self.ftp_over_tls = None
        self.storage_size = None
        self.total_size = 0

        self.ftp_host = None

        self.lock = Lock()

    def connect(self, host, port, user=None, password=None, active=None, ftp_over_tls=False,
                debug=False, storage_size=None):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.active = active
        self.ftp_over_tls = ftp_over_tls
        self.storage_size = storage_size

        class MyFTP_TLS(ftplib.FTP_TLS):
            """Explicit FTPS, with shared TLS session"""

            def ntransfercmd(self, cmd, rest=None):
                conn, size = ftplib.FTP.ntransfercmd(self, cmd, rest)
                if self._prot_p:
                    session = self.sock.session
                    if isinstance(self.sock, ssl.SSLSocket):
                        session = self.sock.session
                    conn = self.context.wrap_socket(conn,
                                                    server_hostname=self.host,
                                                    session=session)  # this is the fix
                return conn, size

        my_session_factory = ftputil.session.session_factory(
            base_class=ftplib.FTP if self.ftp_over_tls is False else MyFTP_TLS,
            port=port,
            encrypt_data_channel=True,
            use_passive_mode=not active,
            encoding="UTF-8",
            debug_level=debug
        )

        try:
            self.ftp_host = ftputil.FTPHost(host, user, password, session_factory=my_session_factory)
        except ftputil.error.PermanentError as e:
            if e.errno in (503, 550):
                raise ConfigurationError(f'Server at {host} requires ftp_over_tls')
            else:
                raise

    def get_storage_size(self, _):
        #this runs at crawl start, so the total size doesn't reflect the filesizes
        return self.storage_size, self.storage_size-self.total_size, self.storage_size-self.total_size

    def abspath(self, path):
        if path != '/':
            path = path.rstrip('/')
        return self.ftp_host.path.abspath(path)

    def check_dirpath(self, path):
        try:
            self.stat(path)
        except ftputil.error.RootDirError:
            return (True, None)
        except ftputil.error.PermanentError as e:
            if e.errno == 550:
                return (False, '{0} no such directory!'.format(path))
            else:
                raise
        return (True, None)

    def walk_ftp(self, top):
        if not top:
            raise ValueError('No top path param')

        dirs = []
        nondirs = []

        for entry in self.scandir_ftp(top):
            if entry.is_dir() is True:
                dirs.append(entry.name)
            else:
                nondirs.append(entry.name)

        yield top, dirs, nondirs

        # Recurse into sub-directories
        for name in dirs:
            new_path = join(top, name)
            for entry in self.walk_ftp(new_path):
                yield entry

    def stat(self, path, st=None):
        if st is None:
            try:
                with self.lock:
                    entry = self.ftp_host.lstat(path)
            except ftputil.error.RootDirError:
                return stat_result(
                    (None, self.user, self.password, 0, 0)
                )

            self.total_size += entry.st_size or 0
            st = (
                entry.st_mode,
                entry.st_uid,
                entry.st_gid,
                entry.st_size,
                entry.st_mtime
            )
        return stat_result(st)

    def scandir_ftp(self, top):
        with self.lock:
            entries = self.ftp_host.listdir(top)

        for name in entries:
            yield FTPDirEntry(top, name, self)

    def close(self, _):
        self.ftp_host.close()


def add_mappings(mappings):
    mappings['mappings']['properties'].update({
        'unix_perms': {
            'type': 'keyword'
        }
    })

def add_meta(_, osstat):
    if osstat.st_mode is None:
        return {'unix_perms': '000'}
    return {'unix_perms': oct(osstat.st_mode)[-3:]}


def add_tags(metadict):
    # check if permissions are fully open and add extra tags
    if metadict['unix_perms'] in ('777', '666'):
        newtags = ['unixperms-plugin', 'ugo+rwx']
        if 'tags' in metadict:
            return {'tags': metadict['tags'] + newtags}
        else:
            return {'tags': newtags}
    return None


ftpserver = FTPServer()

walk = ftpserver.walk_ftp
scandir = ftpserver.scandir_ftp
check_dirpath = ftpserver.check_dirpath
abspath = ftpserver.abspath
get_storage_size = ftpserver.get_storage_size
stat = ftpserver.stat
close = ftpserver.close
