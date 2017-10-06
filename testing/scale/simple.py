from locust import TaskSet, Locust, task
import boto3


ddb_east = boto3.client('dynamodb', region_name='us-east-1')   


class Inserter(TaskSet):

    @task(1)
    def insert(self):
        DataLoad.id += 1
        print 'insert {}'.format(DataLoad.id)

        response = ddb_east.put_item(
            TableName='PKTestTable',
            Item={
                "Id": {
                    "S": 'id - {}'.format(DataLoad.id)
                },
                "ts": {
                    "N": str(10)
                },
                "wid": {
                    "S": 'wid{}'.format(DataLoad.id)
                },
                "replicate": {
                    "BOOL": True
                },
                "region": {
                    "S":"from the east"
                }
            }
        )

        print 'insert complete'

class DataLoad(Locust):
    id = 0
    task_set = Inserter
    min_wait=1000
    max_wait=5000