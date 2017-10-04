import boto3
import os
import datetime
import time
import json
import uuid
from botocore.exceptions import ClientError

# Table config from environment
dest_table = os.environ['DEST_TABLE']
dest_region = os.environ['DEST_REGION']
stack_name = os.environ['STACK_NAME']

# Use metric namespace unique to the stack
metric_namespace = 'XtRepl' + stack_name

# SDK handles
sqs = boto3.client('sqs')
ddb = boto3.client('dynamodb',region_name=dest_region)
cw = boto3.client('cloudwatch')

def pub_statistic(name):
    response = cw.put_metric_data(
            Namespace=metric_namespace,
            MetricData=[
                {
                    'MetricName': name,
                    'Dimensions': [
                        {
                            'Name':'table',
                            'Value': dest_table
                        }
                    ],
                    'Timestamp' : datetime.datetime.utcnow(),
                    'Value':1.0,
                    'Unit': 'Count'
                }
            ]
        )
    print response


def hash_attribute(table_name):
    response = ddb.describe_table(
        TableName=table_name
    )
    
    table = response['Table']
    keySchema = table['KeySchema']
    
    for keyAttr in keySchema:
        if keyAttr['KeyType'] == 'HASH':
            return keyAttr['AttributeName']

def id_not_exists_condition(table_name):
    hash_attr = hash_attribute(table_name)
    return 'attribute_not_exists({})'.format(hash_attr)


def replicate_this(event):
    if event['eventName'] != 'REMOVE' and not ('replicate' in event['dynamodb']['NewImage']):
        return False
    else:
        return True

def insert(body):
    newImage = body['newImage']
    print 'insert {}'.format(newImage)

    body_ts = newImage['ts']
    body_wid = newImage['wid']

    try:
        response = ddb.put_item(
            TableName=dest_table,
            Item=newImage,
            ConditionExpression='{} OR ((:ts > ts) OR (:ts = ts AND :wid > wid))'.format(id_not_exists_condition(dest_table)),
            ExpressionAttributeValues={
                ':ts': body_ts,
                ':wid': body_wid
            }
        )
    except ClientError as e:
        pub_statistic('ReplicatedInsertErrorCount')
        if e.response['Error']['Code'] == "ConditionalCheckFailedException":
            print 'unable to replicate insert: item with key {} exists in remote region'.format(body['keys'])
        else:
            raise
    else:
        print 'insert succeeded'
        pub_statistic('ReplicatedInsertCount')

   

def modify(body):
    newImage = body['newImage']
    print 'modify using {}'.format(newImage)

    body_ts = newImage['ts']
    body_wid = newImage['wid']

    try:
        response = ddb.put_item(
            TableName=dest_table,
            Item=newImage,
            ConditionExpression='{} OR ((:ts > ts) OR (:ts = ts AND :wid > wid))'.format(id_not_exists_condition(dest_table)),
            ExpressionAttributeValues={
                ':ts': body_ts,
                ':wid': body_wid
            }
        )
    except ClientError as e:
        pub_statistic('ReplicatedModifyErrorCount')
        if e.response['Error']['Code'] == "ConditionalCheckFailedException":
            print 'unable to replicate modify with ts {} and wid {}'.format(body_ts, body_wid)
        else:
            raise
    else:
        print 'modify succeeded'
        pub_statistic('ReplicatedModifyCount')

def remove(body):
    keys = body['keys']
    print 'remove {}'.format(keys)

    oldImage = body['oldImage']
    body_ts = oldImage['ts']

    try:
        response = ddb.delete_item(
            TableName=dest_table,
            Key=keys,
            ConditionExpression='{} OR (:ts >= ts)'.format(id_not_exists_condition(dest_table)),
            ExpressionAttributeValues={
                ':ts': body_ts
            }
        )
    except ClientError as e:
        pub_statistic('ReplicatedRemoveErrorCount')
        if e.response['Error']['Code'] == "ConditionalCheckFailedException":
            print 'unable to replicate delete due to conditional check failed (key {})'.format(keys)
        else:
            raise
    else:
        print 'remove succeeded'
        pub_statistic('ReplicatedRemoveCount')
   


def process_body(msg):
    print 'handle {}'.format(msg)
    body = json.loads(msg)

    opcode = body['opcode']

    if opcode == 'INSERT':
        insert(body)
    elif opcode == 'MODIFY':
        modify(body)
    elif opcode == 'REMOVE':
        remove(body)
    else:
        print 'Unknown opcode: {}'.format(opcode)  

def to_timestamp(dt, epoch=datetime.datetime(1970,1,1)):
    td = dt - epoch
    # return td.total_seconds()
    return (td.microseconds + (td.seconds + td.days * 86400) * 10**6) / 10**6



def event_to_body_ctx(record):
    ddbCtx = {}

    now = datetime.datetime.utcnow()
    ddbCtx['timestamp'] = to_timestamp(now)
    ddbCtx['opcode'] = record['eventName']
    ddbCtx['keys'] = record['dynamodb']['Keys']
    if 'NewImage' in record['dynamodb']:
        ddbCtx['newImage'] = record['dynamodb']['NewImage']
    if 'OldImage' in record['dynamodb']:
        ddbCtx['oldImage'] = record['dynamodb']['OldImage']
    ddbCtx['writeId'] = str(uuid.uuid4())

    # Important: we need to remove the replicate property, otherwise
    # when we update remote copies, they would replicate it back to use. 
    # The cycle would be broken by the merge conflict detection,
    # but we want o eliminate the extra processing and cost up 
    # front when possible.
    if 'newImage' in ddbCtx:
        ddbCtx['newImage'].pop('replicate',None)

    return ddbCtx


def lambda_handler(event, context):
    print 'event: {}'.format(event)
    print 'context: {}'.format(context)
    
    event_records = event['Records']
    for r in event_records:
        print 'event name: {}'.format(r['eventName'])
        
        if(not replicate_this(r)):
            print '---> replication not indicated'
            continue
        
        ctx = event_to_body_ctx(r)
        print 'replicate with ctx {}'.format(ctx)