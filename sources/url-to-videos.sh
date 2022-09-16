#!/usr/bin/env bash

# made from a function in:
# https://github.com/pystardust/ani-cli/blob/master/ani-cli

gogohd_url="https://gogohd.net/"
agent="Mozilla/5.0 (X11; Linux x86_64; rv:99.0) Gecko/20100101 Firefox/100.0"
refr="$gogohd_url"
dpage_url=$1
id=$(printf "%s" "$dpage_url" | sed -nE 's/.*id=([^&]*).*/\1/p')
resp="$(curl -A "$agent" -sL "${gogohd_url}streaming.php?id=$id" |
		sed -nE 's/.*class="container-(.*)">/\1/p ;
			s/.*class="wrapper container-(.*)">/\1/p ;
			s/.*class=".*videocontent-(.*)">/\1/p ;
			s/.*data-value="(.*)">.*/\1/p ;
			s/.*data-status="1".*data-video="(.*)">.*/\1/p')"
secret_key=$(printf "%s" "$resp" | sed -n '2p' | tr -d "\n" | od -A n -t x1 | tr -d " |\n")
iv=$(printf "%s" "$resp" | sed -n '3p' | tr -d "\n" | od -A n -t x1 | tr -d " |\n")
second_key=$(printf "%s" "$resp" | sed -n '4p' | tr -d "\n" | od -A n -t x1 | tr -d " |\n")
token=$(printf "%s" "$resp" | head -1 | base64 -d | openssl enc -d -aes256 -K "$secret_key" -iv "$iv" | sed -nE 's/.*&(token.*)/\1/p')
ajax=$(printf '%s' "$id" | openssl enc -e -aes256 -K "$secret_key" -iv "$iv" -a)
data=$(curl -A "$agent" -sL -H "X-Requested-With:XMLHttpRequest" "${gogohd_url}encrypt-ajax.php?id=${ajax}&alias=${id}&${token}" | sed -e 's/{"data":"//' -e 's/"}/\n/' -e 's/\\//g')
result_links="$(printf '%s' "$data" | base64 -d 2>/dev/null | openssl enc -d -aes256 -K "$second_key" -iv "$iv" 2>/dev/null | sed -e 's/\].*/\]/' -e 's/\\//g' | grep -Eo 'https://[-a-zA-Z0-9@:%._\+~#=][a-zA-Z0-9][-a-zA-Z0-9@:%_\+.~#?&\/\/=]*')"
printf "%s\n" $result_links
