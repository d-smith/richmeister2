var AWS = require('aws-sdk');

let numRecords = 0;
let processed = 0;

const handleRecord = (record,callback) => {
    console.log('handle the record');
    
    if(record.eventName != 'REMOVE' && record.dynamodb.NewImage.replicate == undefined) {
            console.log('Replication not indicated',record.dynamodb.Keys)
            checkDone(context);
    } else {
        console.log('replicate');
        replicateRecord(record, callback);
    }
    
    
}

const allProcessed = (callback) => {
    console.log('done processing');
    callback(null, 'yeah ok');
}

const checkDone = (callback) => {
    processed += 1;
    if(processed == numRecords) {
        allProcessed(callback);
    }
}

const replicateRecord = (record, callback) => {
    if (record.eventName == 'INSERT') {
        doInsert(record, callback);
    } else if (record.eventName == 'MODIFY') {
        doModify(record, callback);
    } else  if (record.eventName == 'REMOVE') {
        doRemove(record, callback);
    } else {
        console.log('unknown opcode: ' + record.eventName);
        checkDone(callback);
    }
}

const doInsert = (record, callback) => {
    console.log('replicate insert');
    checkDone(callback);
}

const doModify = (record, callback) => {
    console.log('replicate modify');
    checkDone(callback);
}

const doRemove = (record, callback) => {
    console.log('replicate remove');
    checkDone(callback);
}

exports.handler = (event, context, callback) => {

    numRecords = event.Records.length;

    for (let record of event.Records) {
        console.log(event);
        handleRecord(record,callback);
    }

    
}