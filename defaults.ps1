$tracker = '157.59.41.247'
$seeders = '157.59.41.247'
$downloaders = '157.59.41.247'
$seederPath = 'E:\Applications\ForVirtualMachine\'
$downloaderPath = 'E:\temp\'
$workDir = 'E:\Code\Python\dcTorrent'
$pythonConfig = '-W ignore::DeprecationWarning'
$pwd = convertto-securestring "Di1!qian" -asplaintext -force
$cred = new-object -typename System.Management.Automation.PSCredential -argumentlist "REDMOND\xiliu",$pwd
$trackerURI = 'http://157.59.41.247:6969/announce'
$torrentsPath = 'E:\fileserver\'
$torrentsServer = 'http://157.59.41.247/fileserver/'
