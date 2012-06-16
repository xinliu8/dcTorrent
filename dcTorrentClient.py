import sys
import httplib
from time import strftime, gmtime, time, sleep
from dcTorrentDefaults import defaultSettings
import socket

tracker = ''
seeders = []
downloaders = []
filename = 'gparted.iso'
adminPort = defaultSettings['adminPort']

def startSeed(ip, torrent):
    request = '/admin?action=seed&torrent={0}'.format(torrent)
    site = ip + ':' + adminPort
    httpGet(site, request)

def stopSeed(ip, torrent):
    request = '/admin?action=stop&role=seed&torrent={0}'.format(torrent)
    site = ip + ':' + adminPort
    httpGet(site, request)

def startDownload(ip, torrent):
    request = '/admin?action=download&torrent={0}'.format(torrent)
    site = ip + ':' + adminPort
    httpGet(site, request)

def stopDownload(ip, torrent):
    request = '/admin?action=stop&role=download&torrent={0}'.format(torrent)
    site = ip + ':' + adminPort
    httpGet(site, request)

def startTrack(ip):
    request = '/admin?action=track&port={0}'.format(defaultSettings['trackerPort'])
    site = ip + ':' + adminPort
    httpGet(site, request)

def stopTrack(ip):
    request = '/admin?action=stop&role=track'
    site = ip + ':' + adminPort
    httpGet(site, request)

def makeTorrent(ip, source):
    request = '/admin?action=maketorrent&source=%s' % source
    site = ip + ':' + adminPort
    httpGet(site, request)

def cleanHistory(ip):
    request = '/admin?action=clean'
    site = ip + ':' + adminPort
    httpGet(site, request)

def httpGet(site, request):
    conn = httplib.HTTPConnection(site)
    print 'Connecting to {0}{1}'.format(site, request)
    conn.request("GET", request)
    try:
        r = conn.getresponse()
        print 'Result is {0} {1} {2}'.format(r.status, r.reason, r.read())
    except:
        print sys.exc_info()[0]

def localhostScenario():
    global tracker, seeders, downloaders, filename
    tracker = '127.0.0.1'
    seeders = ['127.0.0.1']
    downloaders = ['127.0.0.1']

def localVMScenario():
    global tracker, seeders, downloaders
    tracker = '157.59.41.247'
    seeders = ['157.59.41.247']
    downloaders = ['157.59.43.63']

def cloudSmallScenario():
    global tracker, seeders, downloaders, filename
    tracker = '10.146.35.100'
    seeders = ['10.146.35.100']
    downloaders = ['10.146.35.120']
    filename = 'longhorn.vhd'

def cloudMiddleScenario():
    global tracker, seeders, downloaders, filename
    tracker = '10.146.35.100'
    seeders = ['10.146.35.100']
    downloaders = ['10.146.35.120', '10.146.35.130', '10.146.35.140', '10.146.37.100', '10.146.37.140', '10.146.39.110', '10.146.39.120', '10.146.39.130']
    filename = 'longhorn.vhd'

def isTrackerUp(tracker):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((tracker, int(defaultSettings['trackerPort'])))
        s.shutdown(2)
        return True    
    except:
        return False

def startAll():
    global tracker, seeders, downloaders, filename
    startTrack(tracker)
    while True:
        sleep(0.2)
        if isTrackerUp(tracker) == True:
            break;

    makeTorrent(tracker, filename)
    torrentUri = "http://{0}:{1}/files/{2}.torrent".format(tracker, adminPort, filename)
    for seeder in seeders:
        startSeed(seeder, torrentUri)
    for downloader in downloaders:
        startDownload(downloader, torrentUri)

def startDownloads():
    global tracker, seeders, downloaders, filename
    torrentUri = "http://{0}:{1}/files/{2}.torrent".format(tracker, adminPort, filename)
    for downloader in downloaders:
        startDownload(downloader, torrentUri)

def stopAll():
    global tracker, seeders, downloaders, filename
    stopTrack(tracker)
    torrentUri = "http://{0}:{1}/files/{2}.torrent".format(tracker, adminPort, filename)
    for seeder in seeders:
        stopSeed(seeder, torrentUri)
    for downloader in downloaders:
        stopDownload(downloader, torrentUri)

def cleanAll():
    global tracker, seeders, downloaders, filename
    cleanHistory(tracker)
    for seeder in seeders:
        cleanHistory(seeder)
    for downloader in downloaders:
        cleanHistory(downloader)

def touchStatLog():
    statfile = open('..\\logs\\stat.log', 'a')
    timestr = strftime('%Y-%m-%d %H:%M:%S UTC', gmtime(time()))
    statfile.write('Job starts at {0}\n'.format(timestr))
    statfile.close()

if __name__ == '__main__':
    localVMScenario()

    if len(sys.argv)==1:
        touchStatLog()
        startAll()
        sys.exit(0)

    if sys.argv[1]=='start':
        touchStatLog()
        startAll()
    elif sys.argv[1]=='startdl':
        touchStatLog()
        startDownloads()
    elif sys.argv[1]=='stop':
        stopAll()
    elif sys.argv[1]=='clean':
        cleanAll()

    
