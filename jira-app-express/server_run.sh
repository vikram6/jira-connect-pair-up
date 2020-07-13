#!/usr/bin/env bash

#npm install

sed -i "s/<IP_HERE>/$(curl http://169.254.169.254/latest/meta-data/public-ipv4)/" config.json

kill $(cat PID)
killall ngrok

#rm -rf nohup.out

nohup npm start &

