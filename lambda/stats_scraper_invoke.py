import boto3


def lambda_handler(event,context):
    client = boto3.client('ecs')
    response = client.run_task(
        cluster='fantasyland-stats-cluster', # name of the cluster
        launchType='FARGATE',
        taskDefinition='fantasyland-stats-scrape:5', # replace with your task definition name and revision
        count=5,
        platformVersion='LATEST',
        networkConfiguration={
            'awsvpcConfiguration': {
                'subnets': [
                    'subnet-0aa551b1390fd869b', # replace with your public subnet or a private with NAT
                    'subnet-09e217d61f51b8b63' # Second is optional, but good idea to have two
                ],
                'assignPublicIp': 'ENABLED',
                'securityGroups': [
                    'sg-0d40dbc06d8603884'

                ]
            }
        })
    return str(response)