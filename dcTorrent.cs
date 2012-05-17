using System.Diagnostics;

namespace CallPython
{
    class Program
    {
        static void Main(string[] args)
        {
        }

        private static void ExecuteCommand(string command, string arguments)
        {
            int exitCode;
            ProcessStartInfo ProcessInfo;
            Process process;

            ProcessInfo = new ProcessStartInfo(command, arguments);
            ProcessInfo.CreateNoWindow = true;
            ProcessInfo.UseShellExecute = false;
            ProcessInfo.RedirectStandardError = true;
            ProcessInfo.RedirectStandardOutput = true;

            process = Process.Start(ProcessInfo);
            process.WaitForExit();

            string output = process.StandardOutput.ReadToEnd();
            string error = process.StandardError.ReadToEnd();

            exitCode = process.ExitCode;

            if (!string.IsNullOrEmpty(output) && !string.IsNullOrWhiteSpace(output))
            {
                Trace.TraceInformation("ExecuteCommand: {0} {1}, output: {2}", command, arguments, output);
            }

            if ((!string.IsNullOrEmpty(error) && !string.IsNullOrWhiteSpace(output)) || exitCode != 0)
            {
                Trace.TraceError("ExecuteCommand: {0} {1}, exitCode: {2}, error: {3}", command, arguments, exitCode, error);
            }

            process.Close();
        }
    }
}

