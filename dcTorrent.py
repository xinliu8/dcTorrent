import sys
from BitTornado.BT1.track import TrackerServer, track

from BitTornado.BT1.makemetafile import make_meta_file, defaults
from BitTornado.parseargs import parseargs
from dcTorrentDownload import HeadlessDownloader
from dcTorrentDownloadMany import HeadlessDownloadMany
from dcTorrentDefaults import defaultDirs, defaultSettings
from time import time, gmtime, strftime
import dcTorrentLogging
import cProfile, logging.config, socket
import os

def make_torrent(filename, dir, trackers):
    source = os.path.join(dir, filename)
    target = os.path.join(dir, filename + '.torrent')
    trackerUris = ['http://{0}:{1}/announce'.format(tracker, defaultSettings['trackerPort']) for tracker in trackers]
    params = [trackerUris[0], source, '--target', target]
    if len(trackerUris) > 1:
        params += ['--announce_list', ','.join(trackerUris[1:])]

    try:
        config, args = parseargs(params, defaults, 2, None)
        for file in args[1:]:
            make_meta_file(file, args[0], config)
    except ValueError, e:
        print 'error: ' + str(e)
        print 'run with no args for parameter explanations'

def make_torrents(dir, trackers):
    for f in os.listdir(dir):
        if not f.endswith('.torrent'):
            make_torrent(f, dir, trackers)

def testSeed(argv):
    argv += ['start', 'seed'];
    #argv += ['--url', 'http://localhost/fileserver/gparted.iso.torrent', '--saveas', 'e:\\Applications\\ForVirtualMachine\\gparted.iso', '--ip', '157.59.41.247']
    argv += ['--responsefile', '..\data\gparted.iso.torrent', '--saveas', '..\data\gparted.iso', '--ip', '127.0.0.1']

def testDownload(argv):
    argv += ['start', 'download'];
    #argv += ['--url', 'http://localhost/fileserver/gparted.iso.torrent', '--saveas', 'e:\\temp\\gparted.iso', '--ip', '157.59.41.247']
    argv += ['--responsefile', '..\data\gparted.iso.torrent', '--saveas', '..\downloaded\gparted.iso']

def testTrack(argv):
    argv += ['start', 'track'];
    argv += ['--port', '6969', '--dfile', 'dstate'];

def testMakeTorrent(argv):
    argv += ['make', 'torrent'];
    argv += ['http://127.0.0.1:6969/announce', '..\data\gparted.iso', '--target', '..\data\gparted.iso.torrent'];

def testMakeTorrents(argv):
    argv += ['make', 'torrents'];
    argv += [defaultDirs['seed']];

def testSeedmany(argv):
    argv += ['start', 'seedmany'];
    argv += [defaultDirs['seedmany'], '--saveas', defaultDirs['seedmany'], '--ip', '127.0.0.1'];

def testDcTorrent(argv):
    target = argv[2]
    argv.remove('test')
    argv.remove(target)
    if  target == 'track':
        testTrack(argv)
    elif target == 'torrent':
        testMakeTorrent(argv)
    elif target == 'seed':
        testSeed(argv)
    elif target == 'download':
        testDownload(argv)
    else:
        print "Wrong test!"

def trackerAnnouceCallback(infohash, ip):
    statfile = open(os.path.join(defaultDirs['log'], 'stat.log'), 'a')
    timestr = strftime('%Y-%m-%d %H:%M:%S UTC', gmtime(time()))
    readableInfohash = ''.join( [ "%02X" % ord( x ) for x in infohash ] )
    statfile.writelines('{0} finish downloading {1} at {2}\n'.format(ip, readableInfohash, timestr))
    statfile.flush()

if __name__ == '__main__':
    
    profiling = False
    #logging.config.fileConfig('logging.conf')

    argv = sys.argv

    if len(argv) == 1:
        testSeedmany(argv);

    if len(argv) == 1:
        print '%s start tracker/seed/peer' % argv[0]
        print '%s make torrent' % argv[0]
        print
        sys.exit(2) # common exit code for syntax error

    if len(argv) == 3 and argv[1] == 'test':
        testDcTorrent(argv);

    if len(argv) > 3:
        if not os.path.exists(defaultDirs['log']):
            os.makedirs(defaultDirs['log'])
        start = argv[1]
        action = argv[2]
        if action == 'track':
            dcTorrentLogging.setRootLogger(os.path.join(defaultDirs['log'], 'track.log'), logging.DEBUG)
            t = TrackerServer(trackerAnnouceCallback)
            t.track(argv[3:])
        elif action == 'torrent':
            source = argv[3]
            filename = os.path.basename(source)
            dir = os.path.dirname(source)
            host = socket.gethostbyname(socket.gethostname())
            trackers = [host]
            make_torrent(filename, dir, trackers)
        elif action == 'torrents':
            # dir, tracker port
            host = socket.gethostbyname(socket.gethostname())
            dir = argv[3]
            trackers = [host]
            make_torrents(dir, trackers)
        elif action == 'seed' or action == 'download':
            dcTorrentLogging.setRootLogger(os.path.join(defaultDirs['log'], '{0}.log'.format(action)), logging.DEBUG)
            h = HeadlessDownloader()
            if profiling:
                cProfile.run('h.download(argv[2:])', os.path.join(defaultDirs['profile'], '{0}.profile'.format(action)))
            else:
                h.download(argv[2:])
            sys.exit(0)
        elif action == 'seedmany' or action == 'downloadmany':
            dcTorrentLogging.setRootLogger(os.path.join(defaultDirs['log'], '{0}.log'.format(action)), logging.DEBUG)
            h = HeadlessDownloadMany()
            h.download(argv[2:])
        else :
            print ' wrong arguments'
            sys.exit(2) # common exit code for syntax error
