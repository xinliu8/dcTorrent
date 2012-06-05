import sys
import httplib
from time import strftime, gmtime, time, sleep

tracker = ''
seeders = []
downloaders = []
adminPort = '5678'
filename = 'gparted.iso'

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
    request = '/admin?action=track&port=6969'
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

def httpGet(site, request):
    conn = httplib.HTTPConnection(site)
    print 'Connecting to {0}{1}'.format(site, request)
    conn.request("GET", request)
    r = conn.getresponse()
    print 'Result is {0} {1}'.format(r.status, r.reason)

def localhostScenario():
    global tracker, seeders, downloaders
    tracker = '157.59.41.247'
    seeders = ['157.59.41.247']
    downloaders = ['157.59.41.247']

def localVMScenario():
    global tracker, seeders, downloaders
    tracker = '157.59.41.247'
    seeders = ['157.59.41.247']
    downloaders = ['157.59.43.63', '157.59.41.247']

def cloudScenario():
    global tracker, seeders, downloaders, filename
    tracker = '10.146.35.100'
    seeders = ['10.146.35.100']
    downloaders = ['10.146.35.100', '10.146.35.120']
    filename = 'python27.zip'

def startAll():
    global tracker, seeders, downloaders, filename
    startTrack(tracker)
    sleep(1)
    makeTorrent(tracker, filename)
    torrentUri = "http://{0}:{1}/files/{2}.torrent".format(tracker, adminPort, filename)
    for seeder in seeders:
        startSeed(seeder, torrentUri)
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

if __name__ == '__main__':
    
    localVMScenario()

    if sys.argv[1]=='start':
        statfile = open('..\\logs\\stat.log', 'a')
        timestr = strftime('%Y-%m-%d %H:%M:%S UTC', gmtime(time()))
        statfile.write('Job starts at {0}\n'.format(timestr))
        statfile.close()
        startAll()
    elif sys.argv[1]=='stop':
        stopAll()

    
