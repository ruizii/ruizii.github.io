We can use `hashcat` rules to generate permutations of our own wordlist. We can do this on a `VM` using `--force`.

```shell
# --force: Makes it work even without GPU, useful for generating wordlists in VMs
# The awk command takes every entry longer chan 8 characters
hashcat --force --stdout ./words.txt -r /usr/share/hashcat/rules/best64.rule | sort -u | awk 'length($0) > 8' > passwords.txt

# We can also chain multiple rules
hashcat --force --stdout ./words.txt -r /usr/share/hashcat/rules/best64.rule -r /usr/share/hashcat/rules/toggle1.rule | sort -u > passwords.txt
```

>[!tip]
>Don't forget to filter by the password policy. Use `awk` or `rg` for this.

#### Example Wordlists

We can try using the [weak corporate passwords wordlist from this repository](https://github.com/insidetrust/statistically-likely-usernames) either on its own for password spraying or using the `hashcat` permutations.

We can also try a wordlist like this:

```
January
February
March
April
May
June
July
August
September
October
November
December
Password
P@ssw0rd
Secret
<hostname>
htb
Autumn
Fall
Spring
Winter
Summer
```