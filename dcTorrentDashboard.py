import sys
import httplib
from time import strftime, gmtime, time, sleep
from dcTorrentDefaults import defaultSettings, defaultDirs
import socket, os
import logging
from random import choice

trackers = []
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

def startSeedMany(ip, dir):
    request = '/admin?action=seedmany&dir={0}'.format(dir)
    site = ip + ':' + adminPort
    httpGet(site, request)

def stopSeedMany(ip, dir):
    request = '/admin?action=stop&role=seedmany&dir={0}'.format(dir)
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

def startDownloadMany(ip, dir):
    request = '/admin?action=downloadmany&dir={0}'.format(dir)
    site = ip + ':' + adminPort
    httpGet(site, request)

def stopDownloadMany(ip, dir):
    request = '/admin?action=stop&role=downloadmany&dir={0}'.format(dir)
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

def makeTorrent(source, trackers):
    request = '/admin?action=maketorrent&source={0}&trackers={1}'.format(source, ','.join(trackers))
    for tracker in trackers:
        site = tracker + ':' + adminPort
        httpGet(site, request)

def makeTorrents(trackers, dir):
    request = '/admin?action=maketorrents&trackers={0}&torrentdir={1}'.format(','.join(trackers), dir)
    for tracker in trackers:
        site = tracker + ':' + adminPort
        httpGet(site, request)

def cleanHistory(ip, role):
    request = '/admin?action=clean&role={0}'.format(role)
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
    global trackers, seeders, downloaders, filename
    trackers = ['127.0.0.1']
    seeders = ['127.0.0.1']
    downloaders = ['127.0.0.1']

def localVMScenario():
    global trackers, seeders, downloaders
    trackers = ['157.59.40.198', '157.59.43.88']
    seeders = ['157.59.40.198']
    downloaders = ['157.59.43.88']

def cloudSmallScenario():
    global trackers, seeders, downloaders, filename
    trackers = ['10.146.35.100']
    seeders = ['10.146.35.100']
    downloaders = ['10.146.35.120']
    filename = 'longhorn.vhd'

def cloudMiddleScenario():
    global trackers, seeders, downloaders, filename
    trackers = ['10.146.35.100']
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

def startController(seed_abs_dir):
    global trackers, seeders, downloaders
    for tracker in trackers:
        startTrack(tracker)

    retry = 0
    maxRetry = 5
    toCheck = list(trackers)
    while retry < maxRetry:
        sleep(0.1)
        retry += 1
        notReady = [ tracker for tracker in toCheck if not isTrackerUp(tracker)]
        if len(notReady) == 0:
            break;
        toCheck = notReady

    if retry==maxRetry:
        return;

    # only one generate torrents
    makeTorrents(trackers[:1], seed_abs_dir)

    for seeder in seeders:
        startSeedMany(seeder, seed_abs_dir)

def startAllSingleFile():
    global trackers, seeders, downloaders, filename
    for tracker in trackers:
        startTrack(tracker)

    retry = 0
    maxRetry = 5
    while retry < maxRetry:
        sleep(0.1)
        retry += 1
        if isTrackerUp(tracker) == True:
            break;
    if retry==maxRetry:
        return;

    makeTorrent(tracker, os.path.join(defaultDirs['seed'], filename))
    torrentUri = "http://{0}:{1}/files/{2}.torrent".format(tracker, adminPort, filename)
    for seeder in seeders:
        startSeed(seeder, torrentUri)
    for downloader in downloaders:
        startDownload(downloader, torrentUri)

def startAll():
    startController()
    startDownloads()

def startDownloads(filename):
    global trackers, seeders, downloaders
    # use one for torrent
    tracker = trackers[0] #choice(trackers)
    torrentUri = "http://{0}:{1}/files/{2}.torrent".format(tracker, adminPort, filename)
    for downloader in downloaders:
        startDownload(downloader, torrentUri)

def stopAllSingleFile():
    global tracker, seeders, downloaders, filename
    stopTrack(tracker)
    torrentUri = "http://{0}:{1}/files/{2}.torrent".format(tracker, adminPort, filename)
    for seeder in seeders:
        stopSeed(seeder, torrentUri)
    for downloader in downloaders:
        stopDownload(downloader, torrentUri)

def stopAll(seed_abs_dir):
    global trackers, seeders, downloaders
    for tracker in trackers:
        stopTrack(tracker)
    for seeder in seeders:
        stopSeedMany(seeder, seed_abs_dir)

def cleanAll():
    global trackers, seeders, downloaders
    for tracker in trackers:
        cleanHistory(tracker, 'track')
    for seeder in seeders:
        cleanHistory(seeder, 'seedmany')
    for downloader in downloaders:
        cleanHistory(downloader, 'download')

def touchStatLog():
    statfile = open(os.path.join(defaultDirs['log'], 'stat.log'), 'a')
    timestr = strftime('%Y-%m-%d %H:%M:%S UTC', gmtime(time()))
    statfile.write('Job starts at {0}\n'.format(timestr))
    statfile.close()

if __name__ == '__main__':
    localhostScenario()

    if len(sys.argv)==1:
        touchStatLog()
        startAll()
        sys.exit(0)

    if sys.argv[1]=='startc':
        if len(sys.argv) > 2:
            startController(sys.argv[2])
        else:
            startController(defaultDirs['seedmany'])
    elif sys.argv[1]=='startd':
        touchStatLog()
        startDownloads(sys.argv[2])
    elif sys.argv[1]=='stop':
        if len(sys.argv) > 2:
            stopAll(sys.argv[2])
        else:
            stopAll(defaultDirs['seedmany'])
    elif sys.argv[1]=='clean':
        cleanAll()

    
