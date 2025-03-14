import boto3
import json
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

service_mapping = {
    'EC2': 'Amazon Elastic Compute Cloud - Compute',
    'RDS': 'Amazon Relational Database Service',
    'Lambda': 'AWS Lambda',
    'S3': 'Amazon Simple Storage Service'
}


def get_named_parameter(event, name):
    """
    주어진 Lambda 이벤트에서 'parameters' 리스트 내의 각 항목을 검사하여,
    지정한 이름(name)과 일치하는 항목의 'value' 값을 반환합니다.
    일치하는 항목이 없으면 None을 반환합니다.

    Parameters:
        event (dict): 'parameters' 키를 포함하는 Lambda 이벤트 딕셔너리.
        name (str): 찾고자 하는 파라미터의 이름.

    Returns:
        찾은 파라미터의 value 값, 만약 일치하는 항목이 없으면 None.
    """
    # Get the value of a specific parameter from the Lambda event
    for param in event['parameters']:
        if param['name'] == name:
            return param['value']
    return None


def get_resource_cost(resource_id, service_type, region):
    """리소스별 비용 조회 (get_cost_and_usage_with_resources 사용)"""
    with_resources_days = 14
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=with_resources_days)

        ec2 = boto3.client('ec2')
        ce = boto3.client('ce')
        # 필요에 따라 태그 정보도 가져옵니다.
        tags = ec2.describe_tags(Filters=[{'Name': 'resource-id', 'Values': [resource_id]}])['Tags']
        name_tag = next((tag['Value'] for tag in tags if tag['Key'] == 'Name'), None)

        response = ce.get_cost_and_usage_with_resources(
            TimePeriod={
                'Start': start_date.strftime('%Y-%m-%d'),
                'End': end_date.strftime('%Y-%m-%d')
            },
            Granularity='MONTHLY',
            Metrics=['UnblendedCost'],
            Filter={
                'And': [
                    {'Dimensions': {'Key': 'REGION', 'Values': [region]}},
                    {'Dimensions': {'Key': 'SERVICE', 'Values': [service_mapping[service_type]]}},
                    {'Dimensions': {'Key': 'RESOURCE_ID', 'Values': [resource_id]}}
                ]
            }
        )
        print("service:", [service_mapping[service_type]])
        print(f"Cost Explorer response for {resource_id}: {response}", flush=True)

        if response['ResultsByTime']:
            return float(response['ResultsByTime'][0]['Total']['UnblendedCost']['Amount'])
        return 0.0

    except Exception as e:
        print(f"Error getting resource cost: {str(e)}")
        return 0.0


def collect_ec2_data(region, account_id):
    """EC2 인스턴스 데이터 수집"""
    print("Collecting EC2 data...")
    try:
        ec2_data = []

        try:
            if not region:
                print("No region specified, collecting data from all regions...")

            # ec2_client = boto3.client('ec2', region_name=region)
            if account_id:
                sts_client = boto3.client('sts')
                assumed_role = sts_client.assume_role(
                    RoleArn=f"arn:aws:iam::{account_id}:role/Administrator",
                    RoleSessionName="EC2ClientSession"
                )

                credentials = assumed_role['Credentials']

                ec2_client = boto3.client(
                    'ec2',
                    region_name=region,
                    aws_access_key_id=credentials['AccessKeyId'],
                    aws_secret_access_key=credentials['SecretAccessKey'],
                    aws_session_token=credentials['SessionToken']
                )
            else:
                ec2_client = boto3.client('ec2', region_name=region)

            response = ec2_client.describe_instances()
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    try:
                        metrics = get_cloudwatch_metrics(
                            instance['InstanceId'],
                            'EC2',
                            region,
                            account_id
                        )
                        '''cost는 권한이 없어 주석 처리 20250311 '''
                        # cost = get_resource_cost(
                        #     instance['InstanceId'],
                        #     'EC2',
                        #     region
                        # )

                        instance_data = {
                            'resource_id': instance['InstanceId'],
                            'service_type': 'EC2',
                            'region': region,
                            'status': instance['State']['Name'],
                            'creation_date': instance['LaunchTime'].strftime('%Y-%m-%d %H:%M:%S'),
                            'last_modified': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'tags': json.dumps({tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}),
                            # 'cost': cost,
                            'details': {
                                'instance_type': instance['InstanceType'],
                                'private_ip': instance.get('PrivateIpAddress', ''),
                                'public_ip': instance.get('PublicIpAddress', ''),
                                'vpc_id': instance.get('VpcId', ''),
                                'subnet_id': instance.get('SubnetId', ''),
                                'metrics': metrics
                            }
                        }
                        ec2_data.append(instance_data)
                    except Exception as e:
                        print(f"Error processing EC2 instance {instance['InstanceId']}: {str(e)}")
                        continue
        except Exception as e:
            print(f"Error processing region {region}: {str(e)}")
        print(ec2_data)
        # DataFrame을 dict 형태로 변환 후 JSON 문자열로 변환
        json_data = json.dumps(pd.DataFrame(ec2_data).to_dict(orient='records'))
        # return {
        #     'statusCode': 200,
        #     'body': json_data
        # }
        return json_data

    except Exception as e:
        print(f"Error collecting EC2 data: {str(e)}")
        return {"statusCode": 500, "body": "Error collecting EC2 data"}


def get_cloudwatch_metrics(resource_id, service_type, region, account_id, period=600):
    """CloudWatch 메트릭 EC2 데이터 수집"""
    try:
        if account_id:
            sts_client = boto3.client('sts')
            assumed_role = sts_client.assume_role(
                RoleArn=f"arn:aws:iam::{account_id}:role/Administrator",
                RoleSessionName="CloudWatchClientSession"
            )

            credentials = assumed_role['Credentials']
            cloudwatch_client = boto3.client(
                'cloudwatch',
                region_name=region,
                aws_access_key_id=credentials['AccessKeyId'],
                aws_secret_access_key=credentials['SecretAccessKey'],
                aws_session_token=credentials['SessionToken']
            )
        else:
            cloudwatch_client = boto3.client('cloudwatch', region_name=region)

        metrics_data = {}
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=1)

        metric_configs = {
            'EC2': {
                'namespace': 'AWS/EC2',
                'dimension_name': 'InstanceId',
                'metrics': [
                    ('CPUUtilization', 'Percent'),
                    ('NetworkIn', 'Bytes'),
                    ('NetworkOut', 'Bytes'),
                    ('DiskReadBytes', 'Bytes'),
                    ('DiskWriteBytes', 'Bytes')
                ]
            },
            'RDS': {
                'namespace': 'AWS/RDS',
                'dimension_name': 'DBInstanceIdentifier',
                'metrics': [
                    ('CPUUtilization', 'Percent'),
                    ('FreeableMemory', 'Bytes'),
                    ('FreeStorageSpace', 'Bytes')
                ]
            }
        }

        if service_type in metric_configs:
            config = metric_configs[service_type]
            dimension = [{'Name': config['dimension_name'], 'Value': resource_id}]

            for metric_name, unit in config['metrics']:
                try:
                    response = cloudwatch_client.get_metric_statistics(  # <-- 여기 수정
                        Namespace=config['namespace'],
                        MetricName=metric_name,
                        Dimensions=dimension,
                        StartTime=start_time,
                        EndTime=end_time,
                        Period=period,
                        Statistics=['Average']
                    )

                    if response['Datapoints']:
                        metrics_data[metric_name] = {
                            'value': round(response['Datapoints'][-1]['Average'], 2),
                            'unit': unit,
                            'datapoints': json.dumps(response['Datapoints'], default=str)
                        }
                except Exception as e:
                    print(f"Error getting metric {metric_name}: {str(e)}")

        return metrics_data

    except Exception as e:
        print(f"Error getting CloudWatch metrics: {str(e)}")
        return {}


def collect_rds_data(region, account_id):
    """RDS 인스턴스 데이터 수집"""
    print("Collecting RDS data...")
    try:
        rds_data = []

        try:
            if not region:
                print("No region specified, collecting data from all regions...")

            if account_id:
                sts_client = boto3.client('sts')
                assumed_role = sts_client.assume_role(
                    RoleArn=f"arn:aws:iam::{account_id}:role/Administrator",
                    RoleSessionName="RDSClientSession"
                )

                credentials = assumed_role['Credentials']

                rds_client = boto3.client(
                    'rds',
                    region_name=region,
                    aws_access_key_id=credentials['AccessKeyId'],
                    aws_secret_access_key=credentials['SecretAccessKey'],
                    aws_session_token=credentials['SessionToken']
                )
            else:
                rds_client = boto3.client('rds', region_name=region)

            response = rds_client.describe_db_instances()
            for instance in response['DBInstances']:
                try:
                    metrics = get_cloudwatch_metrics(
                        instance['DBInstanceIdentifier'],
                        'RDS',
                        region,
                        account_id
                    )
                    # ''' cost는 권한이 없어 주석 처리 20250311 '''
                    # cost = get_resource_cost(
                    #     instance['InstanceId'],
                    #     'EC2',
                    #     region
                    # )
                except Exception as e:
                    print(f"Error processing RDS instance {instance['DBInstanceIdentifier']}: {str(e)}")
                    continue
                # print("RDS", instance)
                instance_data = {
                    'resource_id': instance['DBInstanceIdentifier'],
                    'service_type': 'RDS',
                    'region': region,
                    'status': instance['DBInstanceStatus'],
                    'creation_date': instance['InstanceCreateTime'].strftime('%Y-%m-%d %H:%M:%S'),
                    'last_modified': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'tags': json.dumps({tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}),
                    # 'cost': cost,
                    'details': {
                        'instance_type': instance['DBInstanceClass'],
                        'engine': instance['Engine'],
                        'engine_version': instance['EngineVersion'],
                        'allocated_storage': instance['AllocatedStorage'],
                        'multi_az': instance['MultiAZ'],
                        'publicly_accessible': instance['PubliclyAccessible'],
                        'vpc_id': instance.get('DBSubnetGroup', {}).get('VpcId', ''),
                        'subnet_id': instance.get('DBSubnetGroup', {}).get('SubnetGroupStatus', ''),
                        'metrics': metrics
                    }
                }
                rds_data.append(instance_data)
                # for instance in reservation['Instances']:
                #     try:
                #         metrics = get_cloudwatch_metrics_rds(
                #             instance['InstanceId'],
                #             'EC2',
                #             region
                #         )
                #         '''cost는 권한이 없어 주석 처리 20250311 '''
                #         # cost = get_resource_cost(
                #         #     instance['InstanceId'],
                #         #     'EC2',
                #         #     region
                #         # )

                #         instance_data = {
                #             'resource_id': instance['InstanceId'],
                #             'service_type': 'EC2',
                #             'region': region,
                #             'status': instance['State']['Name'],
                #             'creation_date': instance['LaunchTime'].strftime('%Y-%m-%d %H:%M:%S'),
                #             'last_modified': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                #             'tags': json.dumps({tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}),
                #             # 'cost': cost,
                #             'details': {
                #                 'instance_type': instance['InstanceType'],
                #                 'private_ip': instance.get('PrivateIpAddress', ''),
                #                 'public_ip': instance.get('PublicIpAddress', ''),
                #                 'vpc_id': instance.get('VpcId', ''),
                #                 'subnet_id': instance.get('SubnetId', ''),
                #                 'metrics': metrics
                #             }
                #         }
                #         ec2_data.append(instance_data)
                #     except Exception as e:
                #         print(f"Error processing EC2 instance {instance['InstanceId']}: {str(e)}")
                #         continue
        except Exception as e:
            print(f"Error processing region {region}: {str(e)}")
        print(rds_data)
        # DataFrame을 dict 형태로 변환 후 JSON 문자열로 변환
        json_data = json.dumps(pd.DataFrame(rds_data).to_dict(orient='records'))
        # return {
        #     'statusCode': 200,
        #     'body': json_data
        # }
        return json_data

    except Exception as e:
        print(f"Error collecting RDS data: {str(e)}")
        return {"statusCode": 500, "body": "Error collecting RDS data"}


def lambda_handler(event, context):
    print(event)
    action_group = event.get('actionGroup', '')
    message_version = event.get('messageVersion', '')
    function = event.get('function', '')

    if function == 'collect_ec2_data':
        region = get_named_parameter(event, "region")
        account_id = get_named_parameter(event, "account_id")
        output = collect_ec2_data(region, account_id)
    elif function == 'collect_rds_data':
        region = get_named_parameter(event, "region")
        account_id = get_named_parameter(event, "account_id")
        output = collect_rds_data(region, account_id)
    else:
        output = 'Invalid function'

    action_response = {
        'actionGroup': action_group,
        'function': function,
        'functionResponse': {
            'responseBody': {'TEXT': {'body': json.dumps(output)}}
        }
    }

    function_response = {'response': action_response, 'messageVersion': message_version}
    print("Response: {}".format(function_response))

    return function_response