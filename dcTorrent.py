from sys import *
from BitTornado.BT1.track import TrackerServer

from BitTornado.BT1.makemetafile import make_meta_file, defaults
from BitTornado.parseargs import parseargs
from dcTorrentDownload import HeadlessDownloader

def makeTorrent(argv):    
    if len(argv) < 2:
        print 'Usage: ' + ' <trackerurl> <file> [file...] [params...]'
        print
        exit(2)

    try:
        config, args = parseargs(argv, defaults, 2, None)
        for file in args[1:]:
            make_meta_file(file, args[0], config)
    except ValueError, e:
        print 'error: ' + str(e)
        print 'run with no args for parameter explanations'

def testSeed(argv):
    argv += ['start', 'seed'];
    argv += ['--url', 'http://localhost/fileserver/gparted.iso.torrent', '--saveas', 'e:\\Applications\\ForVirtualMachine\\gparted.iso', '--ip', '157.59.41.247']

def testPeer(argv):
    argv += ['start', 'peer'];
    argv += ['--url', 'http://localhost/fileserver/gparted.iso.torrent', '--saveas', 'e:\\temp\\gparted.iso', '--ip', '127.0.0.1']

def testTracker(argv):
    argv += ['start', 'tracker'];
    argv += ['--port', '6969', '--dfile', 'dstate'];
    
def testMakeTorrent(argv):
    argv += ['make', 'torrent'];
    argv += ['http://localhost:6969/announce', 'e:\\Applications\\ForVirtualMachine\\gparted.iso', '--target', 'e:\\fileserver\\gparted.iso.torrent'];

def testDcTorrent(argv):
    target = argv[2]
    argv.remove('test')
    argv.remove(target)
    if  target == 'tracker':
        testTracker(argv)
    elif target == 'torrent':
        testMakeTorrent(argv)
    elif target == 'seed':
        testSeed(argv)
    elif target == 'peer':
        testPeer(argv)
    else:
        print "Wrong test!"

if __name__ == '__main__':

    #testPeer(argv);
    
    if len(argv) == 1:
        print '%s start tracker/seed/peer' % argv[0]
        print '%s make torrent' % argv[0]
        print
        exit(2) # common exit code for syntax error
    
    if len(argv) == 3 and argv[1] == 'test':
        testDcTorrent(argv);

    if len(argv) > 3:
        verb = argv[1]
        target = argv[2]
        if target == 'tracker':
            t = TrackerServer()
            t.track(argv[3:])
        elif target == 'torrent':
            makeTorrent(argv[3:])
        elif target == 'seed' or target == 'peer':
            h = HeadlessDownloader()
            h.download(argv[2:])
        else : 
            print ' wrong arguments'
            exit(2) # common exit code for syntax error
