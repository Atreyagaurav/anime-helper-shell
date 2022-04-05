#!/usr/bin/env bash

# made from a function in:
# https://github.com/pystardust/ani-cli/blob/master/ani-cli

link=$(curl -s $1 | sed -n -E 's/.*class="active" rel="1" data-video="([^"]*)".*/\1/p' | sed 's/^/https:/g')

secret_key='3633393736383832383733353539383139363339393838303830383230393037'
iv='34373730343738393639343138323637'
ajax_url="https://gogoplay4.com/encrypt-ajax.php"
crypto_data=$(curl -s "$link" | sed -nE 's/.*data-value="([^"]*)".*/\1/p')
id=$(printf '%s' "$crypto_data" | base64 -d | openssl enc -d -aes256 -K "$secret_key" -iv "$iv" | cut -d '&' -f1)

#encrypt and create the final ajax
ajax=$(echo $id|openssl enc -e -aes256 -K "$secret_key" -iv "$iv" | base64)

data=$(curl -s -H "X-Requested-With:XMLHttpRequest" "$ajax_url" -d "id=$ajax" | sed -e 's/{"data":"//' -e 's/"}/\n/' -e 's/\\//g')

printf '%s' "$data" | base64 -d | openssl enc -d -aes256 -K "$secret_key" -iv "$iv" | sed -e 's/\].*/\]/' -e 's/\\//g' |
    grep -Eo 'https:\/\/[-a-zA-Z0-9@:%._\+~#=][a-zA-Z0-9][-a-zA-Z0-9@:%_\+.~#?&\/\/=]*'
