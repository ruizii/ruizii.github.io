---
created: 2025-09-12
---

📅 `2025-09-12`

#nosql-injection #cred-hunting #password-manager #reverse-engineering #docker

----

## 🖥️ Box Info

| ️🏷️ Name         |  `Shoppy`   |
| --------------- | --- |
| 📆 Release Date |  `2022-09-17`   |
| 🌐 IP Address   |   `10.10.11.180`  |
| 🖥️ OS           |   `Linux`  |
| 🎯 Difficulty   |   `Easy`  |

----

## 🧠 Summary


**🧩 Key Concepts:** 

- `NoSQL` injection
- Password hunting in chat
- Reverse engineering
- `Docker` group

**🛠️ Tools:**  

- `hashcat`

----

## 🌐 Port Scan

- **TCP**: 22, 80, 9093

---

## 🔍 Enumeration

Port 9093 serves `prometheus` metrics for the `Go` backend, but nothing useful. The main site redirects to `http://shoppy.htb`, which I added to `/etc/hosts`. Fuzzing for subdomains, I found `mattermost.shoppy.htb` and I added it too. It's a login page for a `Mattermost` chat. I had no credentials and found no vulnerabilities, so I started enumerating the main site.

I navigated to `/admin` and got redirected to `/login`, which had this login panel:

![[Pasted image 20250912112717.png]]

It looks like a custom login panel, so I tried injections. A `'` caused timeout errors, which suggested my input was reaching the backend database, but `SQL` injection payloads didn't work. A hint pointed to `NoSQL` injection.

After trying some payloads, this one worked.

![[Pasted image 20250912112910.png]]

A username is required. Without one we get the invalid credentials error message.

![[Pasted image 20250912112951.png]]

I swapped the cookies with Cookie Editor and navigated to `/admin`.

![[Pasted image 20250912113217.png]]

The admin panel has a single function, which is to search for users. The search term is sent to the backend through the `username` `URL` parameter.

![[Pasted image 20250912113314.png]]

---

## 🪜 Foothold / User

Adding a single quote to the search term causes an internal server error.

![[Pasted image 20250912113540.png]]

This hints at injection. `sqlmap` found nothing, so I tried `NoSQL` injection, which worked again.

![[Pasted image 20250912113826.png]]

![[Pasted image 20250912113833.png]]

We got users `admin` and `josh`, along with their hashes, which look like `MD5`. They're probably for the `Mattermost` chat, so I tried to crack them.

`josh`'s password cracked, but `admin`'s didn't.

- `josh`:`remembermethisway`

The credentials worked on the `Mattermost` app, but not over `SSH`.

![[Pasted image 20250912114132.png]]

While enumerating the chat, I found this:

![[Pasted image 20250912114200.png]]

I tried these credentials over `SSH`.

- `jaeger`:`Sh0ppyBest@pp!`

And they worked. Got user.

```shell
ssh jaeger@shoppy.htb
jaeger@shoppy.htb's password: 
jaeger@shoppy:~$ ls
Desktop  Documents  Downloads  Music  Pictures  Public  ShoppyApp  shoppy_start.sh  Templates  user.txt  Videos
```

---

## 🛡️ Privilege Escalation

```
jaeger@shoppy:~$ sudo -l 
[sudo] password for jaeger: 
Matching Defaults entries for jaeger on shoppy:
    env_reset, mail_badpass, secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin

User jaeger may run the following commands on shoppy:
    (deploy) /home/deploy/password-manager
```

We had `sudo` permissions as user `deploy` for a custom password manager. I downloaded it to my attack host and used `gdb` to check whether the password was hardcoded. It was: `Sample`.

![[Pasted image 20250912120103.png]]

It worked.

```shell
jaeger@shoppy:/home/deploy$ sudo -u deploy /home/deploy/password-manager
Welcome to Josh password manager!
Please enter your master password: Sample
Access granted! Here is creds !
Deploy Creds :
username: deploy
password: Deploying@pp!
```

I switched to user `deploy`.

```shell
jaeger@shoppy:/home/deploy$ su - deploy 
Password: 
$ whoami
deploy
```

The user is a member of the `docker` group, which is an easy path to root.

```shell
$ groups
deploy docker
```

Let's just get root.

```
$ docker run -it --rm -v /:/mnt alpine chroot /mnt bash

root@3faa390450f7:/# whoami
root
root@3faa390450f7:/# cd root
root@3faa390450f7:~# ls
root.txt
```

Rooted.
