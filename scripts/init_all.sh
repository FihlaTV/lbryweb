#!/bin/bash

set -x

git clone git@github.com:lbryio/lbryweb.git
git clone git@github.com:sayplastic/lbryinc.git
git clone git@github.com:sayplastic/lbry-redux.git
git clone git@github.com:sayplastic/lbry-desktop.git

function finish {
    if [ -n "$cookiejar" ]; then
    	rm "$cookiejar"
    fi

	(
		cd lbryinc
		yarn unlink
	)
	(
		cd lbry-redux
		yarn unlink
	)
	(
		cd lbryweb
		docker-compose down
	)
}
trap finish EXIT


(
	cd lbryweb
	scripts/init_containers.sh &
)


echo "Waiting for registration page to be live"
until curl -s localhost:8000 | grep -q registration; do echo "waiting..."; sleep 5; done

echo "Waiting 30 seconds for wallet to start"
sleep 20

# get account id
cookiejar=$(mktemp)
user=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 4 | head -n 1)
csrf="$(curl -s http://localhost:8000/registration/ --cookie-jar "$cookiejar" | grep csrf | cut -d'"' -f6)"
ACCOUNT_ID=$(curl -s 'http://localhost:8000/registration/' -L --cookie "$cookiejar" -H 'Content-Type: application/x-www-form-urlencoded' --data "csrfmiddlewaretoken=${csrf}&email=$user%40example.com&password1=test&password2=test" | grep 'registered' | cut -d'>' -f 3 | cut -d'<' -f1)




(
	cd lbry-redux
	yarn
	perl -pi -e "s/'X\-Lbrynet\-Account\-Id': '\w+'/'X\-Lbrynet\-Account\-Id': '${ACCOUNT_ID}'/" src/lbry.js
	yarn build
	yarn unlink # if necessary
	yarn link
)


(
	cd lbryinc
	yarn
	yarn unlink # if necessary
	yarn link lbry-redux
	yarn build
	yarn link
)


(
	cd lbry-desktop
	git checkout videojs
	yarn link lbry-redux
	yarn link lbryinc
	yarn
	yarn dev
)
