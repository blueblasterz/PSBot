#!/bin/sh
VeName=BuildVeTpsBot
debver=bullseye
lxc stop $VeName #scrap
lxc delete $VeName
lxc launch images:debian/$debver $VeName
	lxc exec $VeName -- sh -c 'apt update &&\
	apt install python3 pip wget -y &&	
	pip install discord python-dotenv&&\
	cd /root&&\
	wget https://raw.githubusercontent.com/blueblasterz/PSBot/main/TPSBot.py &&\
	echo "run()" >> TPSBot.py &&\
	echo "python3 TPSBot.py" > /root/run'
lxc export $VeName ${VeName}.ve && lxc stop $VeName && lxc delete $VeName