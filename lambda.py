from datetime import datetime
import pandas as pd
import boto3

def handle_insert(record):
    print("Handling Insert: ", record)
    dict = {}

    for key, value in record['dynamodb']['NewImage'].items():
        for dt, col in value.items():
            dict.update({key: col})

    dff = pd.DataFrame([dict])
    dff['EventType'] = record['eventName']
    return dff

def handle_modify(record):
    print("Handling Modify: ", record)
    dict = {}

    for key, value in record['dynamodb']['NewImage'].items():
        for dt, col in value.items():
            dict.update({key: col})

    dff_insert = pd.DataFrame([dict])
    dff_insert['EventType'] = "INSERT"

    dict = {}

    for key, value in record['dynamodb']['OldImage'].items():
        for dt, col in value.items():
            dict.update({key: col})

    dff_remove = pd.DataFrame([dict])
    dff_remove['EventType'] = "REMOVE"

    return pd.concat([dff_insert, dff_remove], ignore_index=True)

def handle_remove(record):
    print("Handle Remove: ", record)
    dict = {}

    for key, value in record['dynamodb']['OldImage'].items():
        for dt, col in value.items():
            dict.update({key: col})

    dff = pd.DataFrame([dict])
    dff['EventId'] = record['eventID']
    dff['EventType'] = record['eventName']
    return dff

def lambda_handler(event, context):
    df = pd.DataFrame()

    for record in event['Records']:
        table = record['eventSourceARN'].split("/")[1]

        if record['eventName'] == "INSERT":
            dff = handle_insert(record)
        elif record['eventName'] == "MODIFY":
            dff = handle_modify(record)
        elif record['eventName'] == "REMOVE":
            dff = handle_remove(record)
        else:
            continue

        if dff is not None:
            dff['created_at'] = record['dynamodb']['ApproximateCreationDateTime']
            df = df.append(dff, sort=True)

    if not df.empty:
        all_columns = list(df)
        df[all_columns] = df[all_columns].astype(str)

        path = table + "_" + str(datetime.now()) + ".parquet"
        print(event)

        df.to_parquet(path, engine='fastparquet', compression='gzip')

        s3 = boto3.client('s3')
        bucketName = "project-de-datewithdata"
        key = "staging/" + table + "/" + table + "_" + str(datetime.now()) + ".parquet"
        print(key)
        
        s3.upload_file(Bucket=bucketName, Key=key, Filename=path)

    print('Successfully processed %s records.' % str(len(event['Records'])))

