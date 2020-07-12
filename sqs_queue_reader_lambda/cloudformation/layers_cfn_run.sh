#!/usr/bin/env bash

aws cloudformation package --template-file layer-template.yaml --output-template-file layer-template-output.yaml --s3-bucket atlassian-hackathon-525499439414
aws cloudformation deploy --template-file layer-template-output.yaml --stack-name atlassian-lambda-deps-layer --capabilities CAPABILITY_NAMED_IAM

