def replicate_this(event):
    if event['eventName'] != 'REMOVE' and not ('replicate' in event['dynamodb']['NewImage']):
        return False
    else:
        return True
        

def lambda_handler(event, context):
    print 'event: {}'.format(event)
    print 'context: {}'.format(context)
    
    event_records = event['Records']
    for r in event_records:
        print 'event name: {}'.format(r['eventName'])
        
        if(not replicate_this(r)):
            print '---> replication not indicated'
            continue
        
        print 'replicate'