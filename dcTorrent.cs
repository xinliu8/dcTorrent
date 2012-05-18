using System.Diagnostics;
using System;
using System.IO;
using System.Threading.Tasks;

namespace CallPython
{
    class Program
    {
        static void Main(string[] args)
        {
            string process = Environment.GetCommandLineArgs()[0];
            string processName = process;
            int index = 0;
            if((index = process.IndexOf('.')) > 0) {
                processName = process.Substring(0, index);
            }
            string verb = args[0];
            string target = args[1];
            string arguments = string.Empty;
            
            if(args.Length > 2)
                arguments = string.Join(" ", args[2]);

            ExecutePythonScripts(processName, verb, target, arguments);
        }

        private static void ExecutePythonScripts(string processName, string verb, string target, string arguments)
        {
            string cmdFileName = processName + target + ".cmd";
            string command = string.Format("python {0}.py {1} {2} {3}", processName, verb, target, arguments);
            using (var file = new StreamWriter(cmdFileName ))
            {
                file.WriteLine(command);
            }

            ExecuteCommand(cmdFileName);
        }

        private static void OutputToFile(StreamReader reader, string fileToWrite)
        {
            string str;
            using ( var writer = new StreamWriter(fileToWrite))
            {
                while((str=reader.ReadLine())!=null)
                {
                    writer.WriteLine(str);
                }
            }
        }

        private static void ExecuteCommand(string command)
        {
            ProcessStartInfo ProcessInfo;
            Process process;

            ProcessInfo = new ProcessStartInfo(command);
            ProcessInfo.CreateNoWindow = true;
            ProcessInfo.UseShellExecute = false;
            ProcessInfo.RedirectStandardError = true;
            ProcessInfo.RedirectStandardOutput = true;

            process = Process.Start(ProcessInfo);
            Task.Factory.StartNew(()=>OutputToFile(process.StandardOutput, command+".log"));
            Task.Factory.StartNew(()=>OutputToFile(process.StandardError, command+".err"));

            process.WaitForExit();
            Console.WriteLine("Process terminated {0}.", command);

            process.Close();
        }
    }
}
