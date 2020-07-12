import boto3
import os
import time

DYNAMODB_URL = os.environ.get('DYNAMODB_URL')


class DDB:
    def __init__(self):
        if DYNAMODB_URL:
            self.dynamodb = boto3.resource('dynamodb', endpoint_url=DYNAMODB_URL)
        else:
            self.dynamodb = boto3.resource('dynamodb')
        self.watson_responses_table_name = 'JiraWatsonResponses'
        self.issues_with_keywords_table_name = 'JiraIssuesWithKeywords'

    def create_table(self, table_name, partition_key, sort_key=None):
        key_schema = [
            {
                'AttributeName': partition_key,
                'KeyType': 'HASH'
            }
        ]
        attribute_definitions = [
            {
                'AttributeName': partition_key,
                'AttributeType': 'S'
            }
        ]
        if sort_key:
            key_schema.append(
                {
                    'AttributeName': sort_key,
                    'KeyType': 'RANGE'
                }
            )
            attribute_definitions.append(
                {
                    'AttributeName': sort_key,
                    'AttributeType': 'S'
                }
            )
        try:
            self.dynamodb.create_table(
                TableName=table_name,
                KeySchema=key_schema,
                AttributeDefinitions=attribute_definitions,
                ProvisionedThroughput={
                    'ReadCapacityUnits': 10,
                    'WriteCapacityUnits': 10
                }
            )
            start = time.time()
            while True:
                table = self.dynamodb.Table(table_name)
                if table.table_status == 'ACTIVE':
                    break
                if time.time() - start > 10:
                    raise Exception("Unable to create table {}".format(table_name))
                time.sleep(1)

            print("Created table {}".format(table_name))
        except Exception as e:
            if type(e).__name__ == 'ResourceInUseException':
                pass
            else:
                raise e

    def batch_write_items(self, table_name, rows):
        table = self.dynamodb.Table(table_name)
        with table.batch_writer() as batch:
            for row in rows:
                batch.put_item(
                    Item=row
                )

    def get_item_from_db(self, table_name, key):
        table = self.dynamodb.Table(table_name)
        response = table.get_item(Key=key)

        return response.get('Item')

    def query(self, table_name, key_condition_expression, attributes_to_get=None):
        table = self.dynamodb.Table(table_name)
        query_kwargs = {
            'KeyConditionExpression': key_condition_expression
        }
        if attributes_to_get:
            query_kwargs['ProjectionExpression'] = attributes_to_get
        done = False
        start_key = None
        while not done:
            if start_key:
                query_kwargs['ExclusiveStartKey'] = start_key
            response = table.query(**query_kwargs)
            items = response.get('Items', [])
            yield items
            start_key = response.get('LastEvaluatedKey', None)
            done = start_key is None

    def scan(self, table_name, attributes_to_get=None):
        table = self.dynamodb.Table(table_name)

        scan_kwargs = {}
        if attributes_to_get:
            scan_kwargs['ProjectionExpression'] = attributes_to_get
        done = False
        start_key = None
        while not done:
            if start_key:
                scan_kwargs['ExclusiveStartKey'] = start_key
            response = table.scan(**scan_kwargs)
            items = response.get('Items', [])
            yield items
            start_key = response.get('LastEvaluatedKey', None)
            done = start_key is None
