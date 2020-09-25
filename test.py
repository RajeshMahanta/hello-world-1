import os
import re
from datetime import datetime, timedelta
import boto3


ACCOUNT_ID = '036801138568'


def lambda_handler(event, context):
    ec2 = boto3.resource("ec2")

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
        if created_at > datetime.now() - timedelta(0):
            young_images.add(image.id)
            
            
    print("Young AMIs {}" .format(young_images)) 

    #Delete old and unused ami
    safe = used_images | young_images
    for image in (
        image for image in my_images if image.id not in safe
    ):
        print('Deregistering {} ({})'.format(image.name, image.id))
        image.deregister()


    # Delete unattached snapshots
    print('Fetching image list')
    images = [image.id for image in ec2.images.filter(Owners=[ACCOUNT_ID],
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
    ]
    print("AMIs after deregistration {}" .format(images))
    print('Deleting snapshots.')
    for snapshot in ec2.snapshots.filter(OwnerIds=[ACCOUNT_ID],
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
    ]):
        print('Checking {}'.format(snapshot.id))
        r = re.match(r".*for (ami-.*) from.*", snapshot.description)
        if r:
            if r.groups()[0] not in images:
                print('Deleting {}'.format(snapshot.id))
                snapshot.delete()
            elif r.groups()[0] in images:
                print('Snapshots in use {}'.format(snapshot.id))
