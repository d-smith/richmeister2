#!/bin/bash
aws dynamodb put-item --table-name serverless-rest-api-with-dynamodb-hc1 \
--item file://insert.json

aws dynamodb put-item --table-name serverless-rest-api-with-dynamodb-hc1 \
--item file://mod.json

aws dynamodb delete-item --table-name serverless-rest-api-with-dynamodb-hc1 \
--key file://key.json