#!/usr/bin/env bash

#npm install

sed -i "s/<IP_HERE>/$(curl http://169.254.169.254/latest/meta-data/public-ipv4)/" config.json

jiraapigwkey=$(aws ssm get-parameter --name "jiraapigwkey" --query "Parameter.Value" --output text --region us-east-1)

export JIRAAPIGWKEY=$jiraapigwkey


kill $(cat PID)
killall ngrok

#rm -rf nohup.out

nohup npm start &

