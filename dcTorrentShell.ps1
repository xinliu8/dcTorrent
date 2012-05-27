. .\defaults.ps1

function Start-Peer($role, $torrent, $filePath, $ip) { 
    $startPeer = {
        param($workDir,$pythonConfig,$role,$torrent,$filePath,$ip) 
        cd $workDir 
        python $pythonConfig dcTorrent.py start $role --url $torrent --saveas $filePath --ip $ip
    }
    
    Invoke-Command $ip $startPeer -argumentlist $workDir,$pythonConfig,$role,$torrent,$filePath,$ip -credential $cred -AsJob
}

function Stop-Peer($role, $torrent, $ip) {
    $stopPeer = {
        param($role, $torrent)
        wmic Path win32_process Where "CommandLine Like '%python%dcTorrent.py start $role --url $torrent%'" Call Terminate
    }

    Invoke-Command $ip $stopPeer -argumentlist $role,$torrent -credential $cred -AsJob
}

function Start-Downloader($torrent, $filePath, $ip){ 
    Start-Peer 'download' $torrent $filePath $ip 
}

function Stop-Downloader($torrent, $ip){ 
    Stop-Peer 'download' $torrent $ip 
}

function Start-Seeder($torrent, $filePath, $ip){ 
    Start-Peer 'seed' $torrent $filePath $ip 
}

function Stop-Seeder($torrent, $ip){ 
    Stop-Peer 'seed' $torrent $ip 
}

function Stop-Tracker { 
    $stopTracker = {  
        param($workDir, $pythonConfig)
        cd $workDir
        python $pythonConfig dcTorrentTrackerService.py stop
        python $pythonConfig dcTorrentTrackerService.py remove 
    }

    Invoke-Command $tracker $stopTracker -argumentlist $workDir,$pythonConfig -credential $cred
}

function Start-Tracker { 
    $startTracker = {
        param($workDir, $pythonConfig)
        cd $workDir
        python $pythonConfig dcTorrentTrackerService.py install
        python $pythonConfig dcTorrentTrackerService.py start 
    }

    Invoke-Command $tracker $startTracker -argumentlist $workDir,$pythonConfig -credential $cred
}

function Make-Torrent ($source, $target, $computerName){

    $makeTorrent = {
        Param($workDir,$pythonConfig,$trackerURI,$source,$target)
        cd $workDir 
        python $pythonConfig dcTorrent.py make torrent $trackerURI $source --target $target
    }

    Invoke-Command $computerName $makeTorrent -ArgumentList $workDir,$pythonConfig,$trackerURI,$source,$target -credential $cred
}

function Start-Seeders($fileName) {
    $source = "$seederPath$fileName"
    $torrentURI = "$torrentsServer$fileName.torrent"
    $torrentLocal = "$torrentsPath$fileName.torrent"
    
    Make-Torrent $source $torrentLocal $tracker
    
    foreach ($seeder in $seeders) {
        Start-Seeder $torrentURI $source $seeder
    }
}

function Stop-Seeders($fileName) {
    $torrentURI = "$torrentsServer$fileName.torrent"
    foreach ($seeder in $seeders) {
        Stop-Seeder $torrentURI $seeder
    }
}

function Start-Downloaders($fileName){
    $dest = $downloaderPath + $fileName
    $torrentURI = "$torrentsServer$fileName.torrent"
    foreach ($downloader in $downloaders) {
        Start-Downloader $torrentURI $dest $downloader
    }
}

function Stop-Downloaders($fileName) {
    $torrentURI = "$torrentsServer$fileName.torrent"
    foreach ($downloader in $downloaders) {
        Stop-Downloader $torrentURI $downloader
    }
}
