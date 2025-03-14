import boto3


def lambda_handler(event, context):
    # 서비스 종류를 받아옵니다.
    service_type = event.get('service_type', 'ec2')  # 기본값은 'ec2'로 설정

    if service_type == 'ec2':
        return get_ec2_status()
    elif service_type == 'rds':
        return get_rds_status()
    elif service_type == 'eks':
        return get_eks_status()
    else:
        return {'error': f'Unsupported service type: {service_type}'}


def get_ec2_status():
    ec2_client = boto3.client('ec2')
    response = ec2_client.describe_instances()

    instance_status = {}
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            instance_status[instance['InstanceId']] = instance['State']['Name']

    return instance_status


def get_rds_status():
    rds_client = boto3.client('rds')
    response = rds_client.describe_db_instances()

    db_instance_status = {}
    for db_instance in response['DBInstances']:
        db_instance_status[db_instance['DBInstanceIdentifier']] = db_instance['DBInstanceStatus']

    return db_instance_status


def get_eks_status():
    eks_client = boto3.client('eks')
    response = eks_client.list_clusters()

    cluster_status = {}
    for cluster_name in response['clusters']:
        cluster_info = eks_client.describe_cluster(name=cluster_name)
        cluster_status[cluster_name] = cluster_info['cluster']['status']

    return cluster_status
