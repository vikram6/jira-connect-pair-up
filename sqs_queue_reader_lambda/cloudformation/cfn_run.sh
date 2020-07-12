#!/usr/bin/env bash

aws cloudformation package --template-file template.yaml --output-template-file template-output.yaml --s3-bucket atlassian-hackathon-525499439414
aws cloudformation deploy --template-file template-output.yaml --stack-name atlassian-sqs-lambda-stack --capabilities CAPABILITY_NAMED_IAM

