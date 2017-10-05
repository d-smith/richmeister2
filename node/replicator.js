var AWS = require('aws-sdk');

let numRecords = 0;
let processed = 0;

const handleRecord = (record,callback) => {
    console.log('handle the record');
    
    if(record.eventName != 'REMOVE' && record.dynamodb.NewImage.replicate == undefined) {
            console.log('Replication not indicated',record.dynamodb.Keys)
    } else {
        console.log('replicate');
    }
    
    processed += 1;
    if(processed == numRecords) {
        allProcessed(callback);
    }
}

const allProcessed = (callback) => {
    console.log('done processing');
    callback(null, 'yeah ok');
}

exports.handler = (event, context, callback) => {

    numRecords = event.Records.length;

    for (let record of event.Records) {
        console.log(event);
        handleRecord(record,callback);
    }

    
}