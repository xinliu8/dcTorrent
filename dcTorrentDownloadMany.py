#!/usr/bin/env python

# Written by John Hoffman
# see LICENSE.txt for license information
import logging
from BitTornado import PSYCO
if PSYCO.psyco:
    try:
        import psyco
        assert psyco.__version__ >= 0x010100f0
        psyco.full()
    except:
        pass

from BitTornado.launchmanycore import LaunchMany
from BitTornado.download_bt1 import defaults, get_usage
from BitTornado.parseargs import parseargs
from threading import Event
from sys import argv, exit
import sys, os
from BitTornado import version, report_email
from BitTornado.ConfigDir import ConfigDir
from dcTorrentDefaults import adjustDownloader

assert sys.version >= '2', "Install Python 2.0 or greater"
try:
    True
except:
    True = 1
    False = 0

def hours(n):
    if n == 0:
        return 'complete!'
    try:
        n = int(n)
        assert n >= 0 and n < 5184000  # 60 days
    except:
        return '<unknown>'
    m, s = divmod(n, 60)
    h, m = divmod(m, 60)
    if h > 0:
        return '%d hour %02d min %02d sec' % (h, m, s)
    else:
        return '%d min %02d sec' % (m, s)

class HeadlessDownloadMany:
    def display(self, data):
        if not data:
            self.logger.debug('no torrents')
        for x in data:
            ( name, status, progress, peers, seeds, seedsmsg, dist,
              uprate, dnrate, upamt, dnamt, size, t, msg ) = x
            self.logger.debug('"%s": "%s" (%s) - %sP%s%s%.3fD u%0.1fK/s-d%0.1fK/s u%dK-d%dK "%s"' % (
                        name, status, progress, peers, seeds, seedsmsg, dist,
                        uprate/1000, dnrate/1000, upamt/1024, dnamt/1024, msg))
        return False
            
    def message(self, s):
        self.logger.info(s)
        
    def exception(self, s):
        self.logger.exception(s)

    # <role> <directory> <global options>
    def download(self, params):
        action = params[0]
        self.logger = logging.getLogger(action)
        
        defaults.extend( [
            ( 'parse_dir_interval', 60,
              "how often to rescan the torrent directory, in seconds" ),
            ( 'save_in', params[1], "directory to save downloads"),
            ( 'saveas_style', 1,
              "How to name torrent downloads (1 = rename to torrent name, " +
              "2 = save under name in torrent, 3 = save in directory under torrent name)" ),
            ( 'display_path', 1,
              "whether to display the full path or the torrent contents for each torrent" ),
        ] )
        try:
            configdir = ConfigDir('launchmany')
            defaultsToIgnore = ['responsefile', 'url', 'priority']
            configdir.setDefaults(defaults,defaultsToIgnore)
            configdefaults = configdir.loadConfig()
            defaults.append(('save_options',0,
             "whether to save the current options as the new default configuration " +
             "(only for btlaunchmany.py)"))
            
            config, args = parseargs(params[1:], defaults, 1, 1, configdefaults)
            if config['save_options']:
                configdir.saveConfig(config)
            configdir.deleteOldCacheData(config['expire_cache_data'])
            if not os.path.isdir(args[0]):
                raise ValueError("Warning: "+args[0]+" is not a directory")
            config['torrent_dir'] = args[0]
        except ValueError, e:
            self.logger.error(str(e) + '\nrun with no args for parameter explanations')
            exit(1)

        for k in adjustDownloader:
            config[k] = adjustDownloader[k]

        LaunchMany(config, self)