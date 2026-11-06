## Theory

AS-REP Roasting targets accounts with Kerberos pre-authentication disabled. It lets us request an AS-REP for the user without their password, then try to crack it offline to recover the password. We can do this with NetExec.

>[!tip]
>It's worth trying at the start of every `AD` engagement, since it's so simple.

## Syntax

The syntax of the tool requires an output file option for the `--asreproast` parameter. This will dump every `ASREProastable` user. The output is `hashcat` and `john` friendly.

```shell
nxc ldap <ip> -u '<user>' -p '<pass>' --asreproast <output_file>
```

>[!tip]
>Anonymous `LDAP` binds are required when passing `-p ''` or no credentials. If anonymous binds aren't allowed, we need to pass a username and password.
