## Theory

`ASREProast` is a technique used to retrieve `TGT`s for users with the setting "Do not require `Kerberos` pre-authentication" enabled without knowing their passwords. It's then possible to crack the ticket to retrieve the user's password. We can do this with `NetExec`.

>[!tip]
>It's worth trying at the start of every `AD` engagement, since it's so simple.

## Syntax

The syntax of the tool requires an output file option for the `--asreproast` parameter. This will dump every `ASREProastable` user. The output is `hashcat` and `john` friendly.

```shell
nxc ldap <ip> -u '<user>' -p '<pass>' --asreproast <output_file>
```

>[!tip]
>Anonymous `LDAP` binds are required when passing `-p ''` or no credentials. If anonymous binds aren't allowed, we need to pass a username and password.
