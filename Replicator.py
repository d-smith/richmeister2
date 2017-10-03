def lambda_handler(event, context):
    print 'event: {}'.format(event)
    print 'context: {}'.format(context)
    
    event_records = event['Records']
    for r in event_records:
        print 'event name: {}'.format(r['eventName'])
        
        if r['eventName'] != 'REMOVE' and not ('replicate' in r['dynamodb']['NewImage']):
            print '--> replication not indicated'
            continue
        
        print '--> replicate'