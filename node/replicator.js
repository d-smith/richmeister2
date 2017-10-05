var AWS = require('aws-sdk');

let numRecords = 0;
let processed = 0;

const handle_event = (event,callback) => {
    console.log('handle the event');
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
    console.log("Yay!");

    numRecords = event.Records.length;

    for (let record of event.Records) {
        console.log('event');
        handle_event(event,callback);
    }

    
}