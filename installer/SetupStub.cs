
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.IO.Compression;
using System.Reflection;
using System.Text;
using System.Threading;
using System.Windows.Forms;
using Microsoft.Win32;

[assembly: AssemblyTitle("PNGTubeRemix-Studio-MCP Setup")]
[assembly: AssemblyProduct("PNGTubeRemix-Studio-MCP")]
[assembly: AssemblyVersion("1.4.7.0")]

namespace StudioSetup
{
    public static class PayloadInstaller
    {
        private static readonly byte[] Magic = Encoding.ASCII.GetBytes("PRMSET01");
        private const string StripPrefix = "PNGTubeRemix-Studio-MCP/";

        public static long ReadPayloadOffset(string exePath)
        {
            using (FileStream fs = new FileStream(exePath, FileMode.Open, FileAccess.Read, FileShare.Read))
            {
                if (fs.Length < 16)
                    throw new InvalidDataException("Installer payload footer missing.");
                fs.Seek(-16, SeekOrigin.End);
                byte[] footer = new byte[16];
                int n = fs.Read(footer, 0, 16);
                if (n != 16)
                    throw new InvalidDataException("Could not read installer footer.");
                for (int i = 0; i < 8; i++)
                {
                    if (footer[8 + i] != Magic[i])
                        throw new InvalidDataException("Corrupt installer payload signature.");
                }
                long offset = BitConverter.ToInt64(footer, 0);
                if (offset <= 0 || offset >= fs.Length - 16)
                    throw new InvalidDataException("Invalid installer payload offset.");
                return offset;
            }
        }

        public static void Install(
            string installDir,
            bool desktopShortcut,
            bool startMenuShortcut,
            bool associateFiles,
            bool registerWindows,
            Action<int, string> onProgress)
        {
            string exePath = Application.ExecutablePath;
            long payloadOffset = ReadPayloadOffset(exePath);

            Directory.CreateDirectory(installDir);

            string tempZip = Path.Combine(Path.GetTempPath(), "prm_setup_" + Guid.NewGuid().ToString("N") + ".zip");
            try
            {
                if (onProgress != null) onProgress(10, "Reading bundled package...");
                using (FileStream src = new FileStream(exePath, FileMode.Open, FileAccess.Read, FileShare.Read))
                {
                    long zipLen = (src.Length - 16) - payloadOffset;
                    src.Seek(payloadOffset, SeekOrigin.Begin);
                    using (FileStream dst = new FileStream(tempZip, FileMode.Create, FileAccess.Write, FileShare.None))
                    {
                        byte[] buf = new byte[1024 * 256];
                        long remaining = zipLen;
                        while (remaining > 0)
                        {
                            int toRead = (int)Math.Min(buf.Length, remaining);
                            int read = src.Read(buf, 0, toRead);
                            if (read <= 0) break;
                            dst.Write(buf, 0, read);
                            remaining -= read;
                        }
                    }
                }

                if (onProgress != null) onProgress(30, "Extracting runtime files...");
                using (ZipArchive archive = ZipFile.OpenRead(tempZip))
                {
                    int total = Math.Max(archive.Entries.Count, 1);
                    int done = 0;
                    foreach (ZipArchiveEntry entry in archive.Entries)
                    {
                        done++;
                        string rel = entry.FullName.Replace('\\', '/');
                        if (rel.StartsWith(StripPrefix, StringComparison.OrdinalIgnoreCase))
                            rel = rel.Substring(StripPrefix.Length);
                        if (string.IsNullOrEmpty(rel) || rel.EndsWith("/"))
                            continue;

                        string outPath = Path.Combine(installDir, rel.Replace('/', Path.DirectorySeparatorChar));
                        string outParent = Path.GetDirectoryName(outPath);
                        if (!string.IsNullOrEmpty(outParent))
                            Directory.CreateDirectory(outParent);

                        using (Stream entryStream = entry.Open())
                        using (FileStream outStream = new FileStream(outPath, FileMode.Create, FileAccess.Write, FileShare.None))
                        {
                            entryStream.CopyTo(outStream);
                        }

                        int pct = 30 + (int)(55.0 * done / total);
                        if (onProgress != null) onProgress(pct, "Installing " + rel + "...");
                    }
                }
            }
            finally
            {
                if (File.Exists(tempZip))
                {
                    try { File.Delete(tempZip); } catch { }
                }
            }

            if (onProgress != null) onProgress(88, "Creating uninstaller...");
            string appExe = Path.Combine(installDir, "PNGTube Remix.exe");
            string uninstallBat = Path.Combine(installDir, "Uninstall.cmd");
            WriteUninstaller(uninstallBat, installDir);

            if (registerWindows)
            {
                if (onProgress != null) onProgress(92, "Registering shortcuts and file types...");
                if (desktopShortcut)
                {
                    string deskLnk = Path.Combine(
                        Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory),
                        "PNGTubeRemix-Studio-MCP.lnk");
                    CreateShortcut(deskLnk, appExe, installDir, "PNGTubeRemix-Studio-MCP v1.4.7");
                }
                if (startMenuShortcut)
                {
                    string smDir = Environment.GetFolderPath(Environment.SpecialFolder.Programs);
                    Directory.CreateDirectory(smDir);
                    string smLnk = Path.Combine(smDir, "PNGTubeRemix-Studio-MCP.lnk");
                    CreateShortcut(smLnk, appExe, installDir, "PNGTubeRemix-Studio-MCP v1.4.7");
                }
                if (associateFiles)
                {
                    RegisterFileAssociation(appExe);
                }
                RegisterUninstallEntry(installDir, appExe, uninstallBat);
            }

            if (onProgress != null) onProgress(100, "Installation complete.");
        }

        private static void WriteUninstaller(string uninstallPath, string installDir)
        {
            StringBuilder sb = new StringBuilder();
            sb.AppendLine("@echo off");
            sb.AppendLine("setlocal");
            sb.AppendLine("echo Uninstalling PNGTubeRemix-Studio-MCP...");
            sb.AppendLine("taskkill /F /IM \"PNGTube Remix.exe\" >nul 2>&1");
            sb.AppendLine("del /F /Q \"%USERPROFILE%\\Desktop\\PNGTubeRemix-Studio-MCP.lnk\" >nul 2>&1");
            sb.AppendLine("del /F /Q \"%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\PNGTubeRemix-Studio-MCP.lnk\" >nul 2>&1");
            sb.AppendLine("reg delete \"HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\PNGTubeRemix-Studio-MCP\" /f >nul 2>&1");
            sb.AppendLine("reg delete \"HKCU\\Software\\Classes\\.pngRemix\" /f >nul 2>&1");
            sb.AppendLine("reg delete \"HKCU\\Software\\Classes\\PNGTubeRemix.Model\" /f >nul 2>&1");
            sb.AppendLine("set \"TARGET=" + installDir + "\"");
            sb.AppendLine("start \"\" /b cmd /c \"timeout /t 2 /nobreak >nul & rmdir /s /q \"%TARGET%\"\"");
            sb.AppendLine("exit /b 0");
            File.WriteAllText(uninstallPath, sb.ToString(), Encoding.ASCII);
        }

        private static void CreateShortcut(string shortcutPath, string targetExe, string workingDir, string description)
        {
            Type shellType = Type.GetTypeFromProgID("WScript.Shell");
            if (shellType == null) return;
            object shell = Activator.CreateInstance(shellType);
            object sc = shellType.InvokeMember("CreateShortcut", BindingFlags.InvokeMethod, null, shell, new object[] { shortcutPath });
            Type scType = sc.GetType();
            scType.InvokeMember("TargetPath", BindingFlags.SetProperty, null, sc, new object[] { targetExe });
            scType.InvokeMember("WorkingDirectory", BindingFlags.SetProperty, null, sc, new object[] { workingDir });
            scType.InvokeMember("Description", BindingFlags.SetProperty, null, sc, new object[] { description });
            scType.InvokeMember("IconLocation", BindingFlags.SetProperty, null, sc, new object[] { targetExe + ",0" });
            scType.InvokeMember("Save", BindingFlags.InvokeMethod, null, sc, null);
        }

        private static void RegisterFileAssociation(string appExe)
        {
            using (RegistryKey extKey = Registry.CurrentUser.CreateSubKey(@"Software\Classes\.pngRemix"))
            {
                if (extKey != null) extKey.SetValue("", "PNGTubeRemix.Model");
            }
            using (RegistryKey clsKey = Registry.CurrentUser.CreateSubKey(@"Software\Classes\PNGTubeRemix.Model"))
            {
                if (clsKey != null) clsKey.SetValue("", "PNGTubeRemix Avatar Model");
            }
            using (RegistryKey icoKey = Registry.CurrentUser.CreateSubKey(@"Software\Classes\PNGTubeRemix.Model\DefaultIcon"))
            {
                if (icoKey != null) icoKey.SetValue("", "\"" + appExe + "\",0");
            }
            using (RegistryKey cmdKey = Registry.CurrentUser.CreateSubKey(@"Software\Classes\PNGTubeRemix.Model\shell\open\command"))
            {
                if (cmdKey != null) cmdKey.SetValue("", "\"" + appExe + "\" \"%1\"");
            }
        }

        private static void RegisterUninstallEntry(string installDir, string appExe, string uninstallBat)
        {
            using (RegistryKey k = Registry.CurrentUser.CreateSubKey(@"Software\Microsoft\Windows\CurrentVersion\Uninstall\PNGTubeRemix-Studio-MCP"))
            {
                if (k == null) return;
                k.SetValue("DisplayName", "PNGTubeRemix-Studio-MCP");
                k.SetValue("DisplayVersion", "1.4.7");
                k.SetValue("Publisher", "PNGTubeRemix Studio MCP");
                k.SetValue("InstallLocation", installDir);
                k.SetValue("DisplayIcon", appExe);
                k.SetValue("UninstallString", "\"" + uninstallBat + "\"");
                k.SetValue("NoModify", 1, RegistryValueKind.DWord);
                k.SetValue("NoRepair", 1, RegistryValueKind.DWord);
            }
        }
    }

    public class SetupForm : Form
    {
        private TextBox pathBox;
        private Button browseBtn;
        private CheckBox desktopChk;
        private CheckBox startMenuChk;
        private CheckBox assocChk;
        private CheckBox launchChk;
        private ProgressBar progressBar;
        private Label statusLbl;
        private Button installBtn;
        private Button cancelBtn;
        private bool finished = false;
        private readonly bool registerWindows;

        public SetupForm(string defaultDir, bool regWin)
        {
            registerWindows = regWin;
            Text = "PNGTubeRemix-Studio-MCP v1.4.7 Setup";
            FormBorderStyle = FormBorderStyle.FixedDialog;
            MaximizeBox = false;
            MinimizeBox = true;
            StartPosition = FormStartPosition.CenterScreen;
            ClientSize = new Size(540, 360);
            BackColor = Color.FromArgb(17, 21, 30);
            ForeColor = Color.FromArgb(235, 240, 248);
            Font = new Font("Segoe UI", 9.5f);

            Label title = new Label();
            title.Text = "PNGTubeRemix-Studio-MCP v1.4.7";
            title.Font = new Font("Segoe UI Semibold", 14.5f);
            title.ForeColor = Color.FromArgb(115, 195, 255);
            title.Location = new Point(24, 18);
            title.AutoSize = true;
            Controls.Add(title);

            Label sub = new Label();
            sub.Text = "Install Studio MCP edition with Dockable Panels, Undo/Redo, Themes & WebSocket API";
            sub.ForeColor = Color.FromArgb(180, 192, 212);
            sub.Location = new Point(24, 48);
            sub.AutoSize = true;
            Controls.Add(sub);

            Label dirLbl = new Label();
            dirLbl.Text = "Destination folder:";
            dirLbl.Location = new Point(24, 84);
            dirLbl.AutoSize = true;
            Controls.Add(dirLbl);

            pathBox = new TextBox();
            pathBox.Text = defaultDir;
            pathBox.Location = new Point(24, 108);
            pathBox.Size = new Size(396, 26);
            pathBox.BackColor = Color.FromArgb(26, 32, 46);
            pathBox.ForeColor = Color.FromArgb(235, 240, 248);
            pathBox.BorderStyle = BorderStyle.FixedSingle;
            Controls.Add(pathBox);

            browseBtn = new Button();
            browseBtn.Text = "Browse...";
            browseBtn.Location = new Point(428, 106);
            browseBtn.Size = new Size(88, 28);
            browseBtn.FlatStyle = FlatStyle.Flat;
            browseBtn.BackColor = Color.FromArgb(34, 42, 60);
            browseBtn.ForeColor = Color.FromArgb(235, 240, 248);
            browseBtn.Click += delegate
            {
                using (FolderBrowserDialog fbd = new FolderBrowserDialog())
                {
                    fbd.SelectedPath = pathBox.Text;
                    if (fbd.ShowDialog(this) == DialogResult.OK)
                    {
                        pathBox.Text = Path.Combine(fbd.SelectedPath, "PNGTubeRemix-Studio-MCP");
                    }
                }
            };
            Controls.Add(browseBtn);

            desktopChk = MakeCheck("Create Desktop shortcut", true, 24, 148);
            startMenuChk = MakeCheck("Create Start Menu shortcut", true, 24, 174);
            assocChk = MakeCheck("Associate .pngRemix files with PNGTubeRemix-Studio-MCP", true, 24, 200);
            launchChk = MakeCheck("Launch PNGTubeRemix-Studio-MCP after installation", true, 24, 226);

            progressBar = new ProgressBar();
            progressBar.Location = new Point(24, 264);
            progressBar.Size = new Size(492, 16);
            progressBar.Minimum = 0;
            progressBar.Maximum = 100;
            Controls.Add(progressBar);

            statusLbl = new Label();
            statusLbl.Text = "Ready to install.";
            statusLbl.ForeColor = Color.FromArgb(165, 215, 255);
            statusLbl.Location = new Point(24, 286);
            statusLbl.Size = new Size(492, 20);
            Controls.Add(statusLbl);

            installBtn = new Button();
            installBtn.Text = "Install";
            installBtn.Location = new Point(320, 314);
            installBtn.Size = new Size(96, 32);
            installBtn.FlatStyle = FlatStyle.Flat;
            installBtn.BackColor = Color.FromArgb(62, 132, 245);
            installBtn.ForeColor = Color.White;
            installBtn.Click += OnInstallClicked;
            Controls.Add(installBtn);

            cancelBtn = new Button();
            cancelBtn.Text = "Cancel";
            cancelBtn.Location = new Point(422, 314);
            cancelBtn.Size = new Size(94, 32);
            cancelBtn.FlatStyle = FlatStyle.Flat;
            cancelBtn.BackColor = Color.FromArgb(34, 42, 60);
            cancelBtn.ForeColor = Color.FromArgb(235, 240, 248);
            cancelBtn.Click += delegate { Close(); };
            Controls.Add(cancelBtn);
        }

        private CheckBox MakeCheck(string text, bool checkedVal, int x, int y)
        {
            CheckBox cb = new CheckBox();
            cb.Text = text;
            cb.Checked = checkedVal;
            cb.Location = new Point(x, y);
            cb.AutoSize = true;
            cb.ForeColor = Color.FromArgb(220, 228, 240);
            Controls.Add(cb);
            return cb;
        }

        private void OnInstallClicked(object sender, EventArgs e)
        {
            if (finished)
            {
                if (launchChk.Checked)
                {
                    string exe = Path.Combine(pathBox.Text.Trim(), "PNGTube Remix.exe");
                    if (File.Exists(exe))
                        Process.Start(exe);
                }
                Close();
                return;
            }

            string targetDir = pathBox.Text.Trim();
            if (string.IsNullOrEmpty(targetDir))
            {
                MessageBox.Show(this, "Please select a valid folder.", Text, MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;
            }

            installBtn.Enabled = false;
            browseBtn.Enabled = false;
            pathBox.Enabled = false;
            desktopChk.Enabled = false;
            startMenuChk.Enabled = false;
            assocChk.Enabled = false;

            bool dShort = desktopChk.Checked;
            bool sShort = startMenuChk.Checked;
            bool assoc = assocChk.Checked;

            Thread worker = new Thread(delegate()
            {
                try
                {
                    PayloadInstaller.Install(targetDir, dShort, sShort, assoc, registerWindows, delegate(int pct, string msg)
                    {
                        BeginInvoke((MethodInvoker)delegate
                        {
                            progressBar.Value = Math.Max(0, Math.Min(100, pct));
                            statusLbl.Text = msg;
                        });
                    });
                    BeginInvoke((MethodInvoker)delegate
                    {
                        finished = true;
                        installBtn.Text = "Finish";
                        installBtn.Enabled = true;
                        cancelBtn.Visible = false;
                    });
                }
                catch (Exception ex)
                {
                    BeginInvoke((MethodInvoker)delegate
                    {
                        installBtn.Enabled = true;
                        browseBtn.Enabled = true;
                        pathBox.Enabled = true;
                        statusLbl.Text = "Installation failed.";
                        MessageBox.Show(this, "Installation error:\n" + ex.Message, Text, MessageBoxButtons.OK, MessageBoxIcon.Error);
                    });
                }
            });
            worker.IsBackground = true;
            worker.Start();
        }
    }

    internal static class Program
    {
        [STAThread]
        private static int Main(string[] args)
        {
            bool silent = false;
            bool noReg = false;
            bool launchAfter = true;
            string defaultDir = Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                "Programs",
                "PNGTubeRemix-Studio-MCP");
            string targetDir = defaultDir;

            foreach (string raw in args)
            {
                string a = raw.Trim();
                if (a.Equals("--silent", StringComparison.OrdinalIgnoreCase) || a.Equals("/S", StringComparison.OrdinalIgnoreCase))
                    silent = true;
                else if (a.Equals("--no-reg", StringComparison.OrdinalIgnoreCase))
                    noReg = true;
                else if (a.Equals("--no-launch", StringComparison.OrdinalIgnoreCase))
                    launchAfter = false;
                else if (a.StartsWith("--dir=", StringComparison.OrdinalIgnoreCase))
                    targetDir = a.Substring(6).Trim('"');
                else if (a.StartsWith("/D=", StringComparison.OrdinalIgnoreCase))
                    targetDir = a.Substring(3).Trim('"');
            }

            if (silent)
            {
                PayloadInstaller.Install(targetDir, true, true, true, !noReg, null);
                if (launchAfter && !noReg)
                {
                    string exe = Path.Combine(targetDir, "PNGTube Remix.exe");
                    if (File.Exists(exe))
                        Process.Start(exe);
                }
                return 0;
            }

            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Application.Run(new SetupForm(targetDir, !noReg));
            return 0;
        }
    }
}
