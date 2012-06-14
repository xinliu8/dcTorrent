import sys
from BitTornado.BT1.track import TrackerServer, track

from BitTornado.BT1.makemetafile import make_meta_file, defaults
from BitTornado.parseargs import parseargs
from dcTorrentDownload import HeadlessDownloader
from dcTorrentDefaults import defaultDirs
from time import time, gmtime, strftime
import logging.config

def makeTorrent(argv):
    if len(argv) < 2:
        print 'Usage: ' + ' <trackerurl> <file> [file...] [params...]'
        print
        sys.exit(2)

    try:
        config, args = parseargs(argv, defaults, 2, None)
        for file in args[1:]:
            make_meta_file(file, args[0], config)
    except ValueError, e:
        print 'error: ' + str(e)
        print 'run with no args for parameter explanations'

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
    statfile = open(defaultDirs['log'] + 'stat.log', 'a')
    timestr = strftime('%Y-%m-%d %H:%M:%S UTC', gmtime(time()))
    readableInfohash = ''.join( [ "%02X" % ord( x ) for x in infohash ] )
    statfile.writelines('{0} finish downloading {1} at {2}\n'.format(ip, readableInfohash, timestr))
    statfile.flush()

if __name__ == '__main__':
    
    logging.config.fileConfig('logging.conf')

    argv = sys.argv

    if len(argv) == 1:
        testSeed(argv);

    if len(argv) == 1:
        print '%s start tracker/seed/peer' % argv[0]
        print '%s make torrent' % argv[0]
        print
        sys.exit(2) # common exit code for syntax error

    if len(argv) == 3 and argv[1] == 'test':
        testDcTorrent(argv);

    if len(argv) > 3:
        verb = argv[1]
        target = argv[2]
        if target == 'track':
            t = TrackerServer(trackerAnnouceCallback)
            t.track(argv[3:])            
        elif target == 'torrent':
            makeTorrent(argv[3:])
        elif target == 'seed' or target == 'download':
            h = HeadlessDownloader()
            h.download(argv[2:])
        else :
            print ' wrong arguments'
            sys.exit(2) # common exit code for syntax error
