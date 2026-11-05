If a host has most of these ports open, it's almost certainly a Domain Controller.

| Port | Service |
| --- | --- |
| 53 | `DNS` |
| 88 | `Kerberos` |
| 135 | `RPC` endpoint mapper |
| 139 | `NetBIOS` session service |
| 389 | `LDAP` |
| 445 | `SMB` |
| 464 | `Kerberos` password change |
| 593 | `RPC` over `HTTP` |
| 636 | `LDAPS` |
| 3268 / 3269 | Global Catalog (`LDAP` / `LDAPS`) |
| 5985 | `WinRM` (often open, not DC-specific) |
| 9389 | `AD` Web Services |
