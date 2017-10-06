var AWS = require('aws-sdk');

const destinationTable = process.env.DEST_TABLE;
const destinationRegion = process.env.DEST_REGION;
const hashAttribute = process.env.HASH_ATTRIBUTE;

var dynamoDb = new AWS.DynamoDB({region: destinationRegion});

let numRecords = 0;
let processed = 0;

const handleRecord = (record,callback) => {
    console.log('handle the record');
    
    if(record.eventName != 'REMOVE' && record.dynamodb.NewImage.replicate == undefined) {
            console.log('Replication not indicated',record.dynamodb.Keys)
            checkDone(callback);
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
    console.log('checkDone processed: ' + processed);
    if(processed >= numRecords) {
        allProcessed(callback);
    }
}

const replicateRecord = (record, callback) => {
    let continueReplication = true;

    //Is replication indicated? Note we can only check on
    //inserts and updates as there is no way to inject replication
    //context on delete
    let image = record.dynamodb.NewImage;
    if (record.eventName == 'REMOVE') {
        image = record.dynamodb.OldImage
    }
    
    if (image.ts == undefined || image.wid == undefined) {
        console.log('Replication requested but ts and/or wid fields not present', image);
        continueReplication = false;
    }

    //Important: we need to remove the replicate property, otherwise when
    //we update remote copies, they would replicate it back to use. The
    //cycle would be broken by the merge conflict detection, but we want
    //to eliminate the extra processing and cost up front when possible.
    if (record.dynamodb.NewImage !== undefined) {
        delete record.dynamodb.NewImage.replicate;
    }


    if(continueReplication == false) {
        checkDone(callback);
    } else if(record.eventName == 'INSERT') {
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
    console.log(JSON.stringify(record));

    const newImage = record.dynamodb.NewImage;
    const ts = newImage.ts;
    const wid = newImage.wid;

    const conditionExpression = `attribute_not_exists(${hashAttribute}) OR ((:ts > ts) OR (:ts = ts AND :wid > wid))`
    const expressionAttributeValues = {":ts":ts, ":wid": wid};

    console.log(JSON.stringify(expressionAttributeValues))

    const params = {
        TableName: destinationTable,
        Item: newImage,
        ConditionExpression: conditionExpression,
        ExpressionAttributeValues: {
            ':ts': ts,
            ':wid': wid
        }
    };

    dynamoDb.putItem(params, (error) => {
        if (error) {
            if(error.code == 'ConditionalCheckFailedException') {
                console.log('Item not replicated due to ConditionalCheckFailedException')
            } else {
                console.error(error);
            }
        }

        checkDone(callback);
    });
}

const doModify = (record, callback) => {
    console.log('replicate modify');

    console.log('replicate insert');
    console.log(JSON.stringify(record));

    const newImage = record.dynamodb.NewImage;
    const ts = newImage.ts;
    const wid = newImage.wid;

    const conditionExpression = `attribute_not_exists(${hashAttribute}) OR ((:ts > ts) OR (:ts = ts AND :wid > wid))`
    const expressionAttributeValues = {":ts":ts, ":wid": wid};

    const params = {
        TableName: destinationTable,
        Item: newImage,
        ConditionExpression: conditionExpression,
        ExpressionAttributeValues: {
            ':ts': ts,
            ':wid': wid
        }
    };

    dynamoDb.putItem(params, (error) => {
        if (error) {
            if(error.code == 'ConditionalCheckFailedException') {
                console.log('Item not replicated due to ConditionalCheckFailedException')
            } else {
                console.error(error);
            }
        }

        checkDone(callback);
    
    });
}

const doRemove = (record, callback) => {
    console.log('replicate remove');

    const oldImage = record.dynamodb.OldImage;
    const ts = oldImage.ts;
    const keys = record.dynamodb.Keys;

    const conditionExpression = `attribute_not_exists(${hashAttribute}) OR (:ts >= ts)`;
    const expressionAttributeValues = {":ts":ts};

    const params = {
        TableName: destinationTable,
        Key: keys,
        ConditionExpression: conditionExpression,
        ExpressionAttributeValues: expressionAttributeValues
    };

    dynamoDb.deleteItem(params, (error) => {
        if (error) {
            if(error.code == 'ConditionalCheckFailedException') {
                console.log('Item not replicated due to ConditionalCheckFailedException')
            } else {
                console.error(error);
            }
        }

        checkDone(callback);
    });

}

exports.handler = (event, context, callback) => {

    processed = 0;
    numRecords = event.Records.length;
    console.log('records to process: ' + numRecords);

    for (let record of event.Records) {
        console.log(event);
        handleRecord(record,callback);
    }

    
}