properties {
    $workDir = 'E:\Code\Python\dcTorrent\'
    $pythonConfig = '-W ignore::DeprecationWarning'
    $tracker = '157.59.41.247'
    $seeders = '157.59.41.247'
    $downloaders = '127.0.0.1'
    $deployFinishMessage = 'Deploy finished!'
    $pwd = convertto-securestring "Di1!qian" -asplaintext -force
    $cred=new-object -typename System.Management.Automation.PSCredential -argumentlist "REDMOND\xiliu",$pwd
}

task Deploy -depends StartTracker, StartSeeders, StartDownloaders{ 
    $deployFinishMessage
}

task StartSeeders -depends StartTracker{ 
    $startSeeder = {
        cd $args[0] 
        python $args[1] dcTorrent.py test seed 
    }

    Invoke-Command $seeders $startSeeder -argumentlist $workDir,$pythonConfig -credential $cred -AsJob
}

task StopSeeders {
    $stopSeeder = {
        wmic Path win32_process Where "CommandLine Like '%python%dcTorrent.py test seed'" Call Terminate
    }

    Invoke-Command $seeders $stopSeeder -credential $cred -AsJob
}

task StartDownloaders -depends StartTracker{ 
    $startDownloader = {
        cd $args[0] 
        python $args[1] dcTorrent.py test peer 
    }

    Invoke-Command $downloaders $startDownloader -argumentlist $workDir,$pythonConfig -credential $cred -AsJob
}

task StopDownloaders {
    $stopDownloader = {
        wmic Path win32_process Where "CommandLine Like '%python%dcTorrent.py test peer'" Call Terminate
    }

    Invoke-Command $downloaders $stopDownloader -credential $cred -AsJob
}


task StopTracker { 
    $stopTracker = {  
        cd $args[0]
        python $args[1] dcTorrentTrackerService.py stop
        python $args[1] dcTorrentTrackerService.py remove 
    }

    Invoke-Command $tracker $stopTracker -argumentlist $workDir,$pythonConfig -credential $cred
}

task StartTracker { 
    $startTracker = {
        cd $args[0]
        python $args[1] dcTorrentTrackerService.py install
        python $args[1] dcTorrentTrackerService.py start 
    }

    Invoke-Command $tracker $startTracker -argumentlist $workDir,$pythonConfig -credential $cred
}


task ? -Description "Helper to display task info" {
	Write-Documentation
}
