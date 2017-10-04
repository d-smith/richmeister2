from radish import given, when, then, step
import os
import boto3
import time


ddb_west = boto3.client('dynamodb', region_name='us-west-2')
ddb_east = boto3.client('dynamodb', region_name='us-east-1')    

@given("an item with id {item_id:S}")
def have_id(step, item_id):
    step.context.id = item_id

@given("range key {rk:d}")
def have_range(step, rk):
    step.context.rk = rk

@given("timestamp {ts:g}")
def have_ts(step, ts):
    step.context.ts = ts

@given("wid {wid:S}")
def have_wid(step, wid):
    step.context.wid = wid

@given("remote item {present:S}")
def remote_item_present(step, present):
    step.context.present = present

@given("remote rk {rrk:d}")
def remote_rk(step, rrk):
    step.context.rrk = rrk

@given("remote ts {rts:g}")
def remote_ts(step, rts):
    step.context.rts = rts

@given("remote wid {rwid:S}")
def remote_wid(step, rwid):
    step.context.rwid = rwid
    setup_remote(step.context)

@when("I replicate the insert")
def do_when(step):
    insert_item_to_replicate(step.context)
    print 'delay to allow replication to occur'
    time.sleep(5)
    print 'end delay'

@then("I expect the remote ts {repts:d}")
def check_ts(step, repts):
    print 'check_ts'
    
    response = ddb_west.get_item(
        TableName='CKTestTable',
        Key={
            "Id": {
                "S": step.context.id
            },
            "Sort": {
                "N": str(step.context.rk)
            }
        }
    )
    print response

    item = response['Item']
    remote_ts = int(item['ts']['N'])

    region = item['region']['S']
    step.context.region = region

    assert remote_ts == repts, "Remote ts is {}, expected {}".format(remote_ts, repts)

    if step.context.present != 'no' and step.context.rk != step.context.rrk:
        check_remote_intact(step.context.id, step.context.rrk)

@then("I expect region to be {region:S}")
def check_region(step, region):
    retrieved_region = step.context.region
    assert retrieved_region == region, "Retrieved region is {}, expected {}".format(retrieved_region, region)

def setup_remote(ctx):
    if ctx.present == 'no':
        return

    response = ddb_west.put_item(
        TableName='CKTestTable',
        Item={
            "Id": {
                "S": ctx.id
            },
            "Sort": {
                "N": str(ctx.rrk)
            },
            "ts": {
                "N": str(ctx.rts)
            },
            "wid": {
                "S": ctx.rwid
            },
            "region": {
                "S":"west"
            }
        }
    )

    print response


def insert_item_to_replicate(ctx):
    response = ddb_east.put_item(
        TableName='CKTestTable',
        Item={
            "Id": {
                "S": ctx.id
            },
            "Sort": {
                "N": str(ctx.rk)
            },
            "ts": {
                "N": str(ctx.ts)
            },
            "wid": {
                "S": ctx.wid
            },
            "replicate": {
                "BOOL": True
            },
            "region": {
                "S":"east"
            }
        }
    )

    print response

def check_remote_intact(id, rrk):

    response = ddb_west.get_item(
        TableName='CKTestTable',
        Key={
            "Id": {
                "S": id
            },
            "Sort": {
                "N": str(rrk)
            }
        }
    )

    print response

    item = response['Item']
    retrieved_region = item['region']['S']
    assert retrieved_region == 'west', "Retrieved region is {}, expected west".format(retrieved_region)
