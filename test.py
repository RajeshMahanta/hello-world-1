import os
import re
from datetime import datetime, timedelta
import boto3
import json
import dateutil
from dateutil import parser
from boto3 import ec2


ACCOUNT_ID = '036801138568'


def lambda_handler(event, context):
    ec2 = boto3.resource("ec2")

    #### OLD UNUSED AMI DELETION ######
    # Gather AMIs and figure out which ones to delete
    my_images = ec2.images.filter(Owners=[ACCOUNT_ID],
    Filters=[
        {
            'Name': 'tag:BillingCostCenter',
            'Values': [
                '789123456',
            ]
        },
        {
            'Name': 'tag:Division',
            'Values': [
                'test',
            ]
        },
    ]
    )

    # Do not delete images in use
    used_images = {
        instance.image_id for instance in ec2.instances.all()
    }
    print("Used AMIs {}" .format(used_images)) 

    # Keep everything younger than forty five days
    young_images = set()
    for image in my_images:
        created_at = datetime.strptime(
            image.creation_date,
            "%Y-%m-%dT%H:%M:%S.000Z",
        )
        if created_at > datetime.now() - timedelta(45):
            young_images.add(image.id)
            
            
    print("Young AMIs {}" .format(young_images)) 

    #Delete old and unused ami
    safe = used_images | young_images
    for image in (
        image for image in my_images if image.id not in safe
    ):
        print('Deregistering {} ({})'.format(image.name, image.id))
        image.deregister()
        
    ####SNAPSHOT DELETION######

    ebsAllSnapshots = ec2.snapshots.filter(OwnerIds=[ACCOUNT_ID],
    Filters=[
        {
            'Name': 'tag:BillingCostCenter',
            'Values': [
                '789123456',
            ]
        },
        {
            'Name': 'tag:Division',
            'Values': [
                'test',
            ]
        },
    ])

    #Get the 30 days old date
    # timeLimit=datetime.datetime.now() - datetime.timedelta(days=0)
    timeLimit = datetime.now() - timedelta(days=45)
    print(timeLimit)
    
    for snapshot in ebsAllSnapshots:
         
        if snapshot.start_time.date() <= timeLimit.date():
            try:
                print('Deleting Snapshot {} ({}) ' .format(snapshot.id, snapshot.tags))
                snapshot.delete()
            except:
                # this section will have all snapshots which is created before retention  days
                print('The Snapshot is less than retention period or is in use {} ({})' .format(snapshot.id, snapshot.tags))
