#!/usr/bin/env bash

# made from a function in:
# https://github.com/pystardust/ani-cli/blob/master/ani-cli

link=$(curl -s $1 | sed -n -E 's/^[[:space:]]*<a href="#" rel="100" data-video="([^"]*)".*/\1/p' | sed 's/^/https:/g')

ajax_url='https://gogoplay.io/encrypt-ajax.php'

#get the id from the url
video_id=$(printf "%s" "$link" | cut -d\? -f2 | cut -d\& -f1 | sed 's/id=//g')

#construct ajax parameters
secret_key='3235373436353338353932393338333936373634363632383739383333323838'
iv='34323036393133333738303038313335'

ajax=$(printf "$video_id" | openssl enc -aes256  -K "$secret_key" -iv "$iv" -a)

#send the request to the ajax url
curl -s -H 'x-requested-with:XMLHttpRequest' "$ajax_url" -d "id=$ajax" -d "time=69420691337800813569" | jq -r '.source[].file'
