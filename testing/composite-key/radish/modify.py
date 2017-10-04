from radish import given, when, then, step
import os

import boto3
import time

ddb_west = boto3.client('dynamodb', region_name='us-west-2')
ddb_east = boto3.client('dynamodb', region_name='us-east-1') 


@given("id and sort {item:S} {sort:d}")
def modify_this_one(step, item, sort):
    print 'modify_this_one'
    response = ddb_east.get_item(
        TableName='CKTestTable',
        Key={
            "Id": {
                "S": item
            },
            "Sort": {
                "N": str(sort)
            }
        }
    )

    print response
    
    ddb_item = response['Item']

    step.context.ddb_item = ddb_item
    step.context.item = item
    step.context.sort = sort

@when("I modify it")
def do_mod(step):
    
    for k in step.context.ddb_item:
        print '{} -> {}'.format(k,step.context.ddb_item[k])

    ddb_item = step.context.ddb_item
    ddb_item['replicate'] = {'BOOL': True}
    
    response = ddb_east.put_item(
        TableName='CKTestTable',
        Item=ddb_item
    )

    print response

@step("replication runs")
def replicate(step):
    print 'delay to allow replication to complete'
    time.sleep(5)
    print 'delay complete'
    

@then("I expect {region:S}")
def verify_mod_rep(step, region):
    print 'verify_mod_rep'

    response = ddb_west.get_item(
        TableName='CKTestTable',
        Key={
            "Id": {
                "S": step.context.item
            },
            "Sort": {
                "N": str(step.context.sort)
            }
        }
    )
    print response

    repl_item = response['Item']

    repl_region = repl_item['region']['S']

    assert repl_region == region, "Remote region is {}, expected {}".format(repl_region, region)