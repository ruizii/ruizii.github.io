We can use `hashcat` rules with `--stdout` to generate variations of every entry in a wordlist (e.g. capitalization, appended numbers, leetspeak).

```shell
# The awk command takes every entry longer chan 8 characters
hashcat --force --stdout ./wordlist.txt -r /usr/share/hashcat/rules/best64.rule | sort -u | awk 'length($0) > 8' > passwords.txt

# We can also chain multiple rules
hashcat --force --stdout ./wordlist.txt -r /usr/share/hashcat/rules/best64.rule -r /usr/share/hashcat/rules/toggle1.rule | sort -u > passwords.txt
```

>[!tip]
>Filter by password policy. Use `awk` or `rg` for this.
