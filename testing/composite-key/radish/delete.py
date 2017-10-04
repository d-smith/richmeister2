from radish import given, when, then, step
import boto3
import time

ddb_west = boto3.client('dynamodb', region_name='us-west-2')
ddb_east = boto3.client('dynamodb', region_name='us-east-1') 

@given("{thing:S} {sort:d} to delete")
def thing_to_delete(step, thing, sort):
    step.context.thing = thing
    step.context.sort = sort
    return

@when("I delete it")
def delete_it(step):
    response = ddb_east.delete_item(
        TableName='CKTestTable',
        Key={
            'Id':{'S':step.context.thing},
            'Sort':{'N':str(step.context.sort)}
        }
    )

    print response


@then("result should be {this:S}")
def result_should_be(step, this):
    print 'delay to allow replication to complete'
    time.sleep(5)
    print 'delay complete'

    response = ddb_west.get_item(
        TableName='CKTestTable',
        Key={
            'Id':{'S':step.context.thing},
            'Sort':{'N':str(step.context.sort)}
        }
    )

    print response

    if this == 'none':
        itemPresent = 'Item' in response
        assert itemPresent == False, "expected no item"
    else:
        item = response['Item']
        repl_region = item['region']['S']
        assert repl_region == this, "expected {} got {}".format(this, repl_region)