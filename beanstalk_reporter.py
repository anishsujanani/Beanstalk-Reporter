'''
Beanstalk-Reporter
-------------------
Reqs:   boto3, python3.x
Usage:  python3 beanstalk_report.py --profile <aws_cli_profile_name> --env <beanstalk_env_name>
Output: JSON to stdout
Author: Anish Sujanani
Date:   November, 2021
'''
import boto3
import sys
import argparse
import json

session = None

def get_resource_info(environment_name):
    eb = session.client('elasticbeanstalk')
    try:
        env_resources = eb.describe_environment_resources(EnvironmentName=environment_name)
    except Exception as _:
        print('Something went wrong when trying to get Beanstalk Environment information.')
        sys.exit(0)
    
    resources = {}
    if len(env_resources['EnvironmentResources']['LoadBalancers']) > 0:
        resources['LoadBalancers'] = get_load_balancer_info(env_resources['EnvironmentResources']['LoadBalancers'])
    if len(env_resources['EnvironmentResources']['AutoScalingGroups']) > 0:
        resources['AutoScalingGroups'] = get_auto_scaling_group_info(env_resources['EnvironmentResources']['AutoScalingGroups'])
    if len(env_resources['EnvironmentResources']['Instances']) > 0:
        resources['Instances'] = get_ec2_instance_info(env_resources['EnvironmentResources']['Instances'])

    return resources

def get_load_balancer_info(env_resources_lb_chunk):
    boto3_lb = session.client('elbv2')
    all_lb_info = {} 

    for lb in env_resources_lb_chunk:
        sec_groups = []
        try:
            lb_info = boto3_lb.describe_load_balancers(LoadBalancerArns=[lb['Name']])
        except Exception as _:
            print('Something went wrong when trying to get LoadBalancer information.')
            sys.exit(0)

        try:
            for i in lb_info['LoadBalancers']:
                lb_json = {}
                lb_json['DNSName'] = i['DNSName']
                lb_json['LoadBalancerName'] = i['LoadBalancerName']
                lb_json['AvailabilityZones'] = []
                for _ in i['AvailabilityZones']:
                    lb_json['AvailabilityZones'].append({'ZoneName': _['ZoneName'], 'SubnetId': _['SubnetId']})
                sec_groups.extend(i['SecurityGroups'])
                lb_json['SecurityGroups'] = sec_groups            
                lb_json['VpcId'] = i['VpcId']
                all_lb_info['Details'] = lb_json
        except Exception as _:
            print('Something went wrong when trying to parse LoadBalancer information.')
            sys.exit(0)
    
        all_lb_info['Attributes'] = {}
        try:
            lb_attr = boto3_lb.describe_load_balancer_attributes(LoadBalancerArn=lb['Name'])
        except Exception as _:
            print('Something went wrong when trying to get LoadBalancer attributes.')
            sys.exit(0)
        for i in lb_attr['Attributes']:
            all_lb_info['Attributes'][i['Key']] = i['Value']

        try:
            lb_lstn = boto3_lb.describe_listeners(LoadBalancerArn=lb['Name'])
        except Exception as _:
            print('Something went wrong when trying to get LoadBalancer listeners.')
            sys.exit(0)
        
        try:
            all_lb_info['Listeners'] = []
            for i in lb_lstn['Listeners']:
                listener = {}
                listener['Protocol'] = i['Protocol']
                listener['Port'] = i['Port']
                listener['TargetGroupStickiness'] = i['DefaultActions'][0]['ForwardConfig']['TargetGroupStickinessConfig']['Enabled']
                all_lb_info['Listeners'].append(listener)
        except Exception as _:
            print('Something went wrong when trying to parse LoadBalancer listener information.')
            sys.exit(0)

        all_lb_info['SecurityGroups'] = []
        if len(sec_groups) > 0:
            for sg in sec_groups:
                all_lb_info['SecurityGroups'].append(get_security_group_info(sg))
        
        return all_lb_info

def get_auto_scaling_group_info(env_resources_asg_chunk):
    boto3_asg = session.client('autoscaling')
    all_asg_info = {}
    
    for asg in env_resources_asg_chunk: 
        try:
            asg_info = boto3_asg.describe_auto_scaling_groups(AutoScalingGroupNames=[asg['Name']])
        except Exception as _:
            print('Something went wrong when trying to get Autoscaling Group information.')
            sys.exit(0)
        
        try:
            for i in asg_info['AutoScalingGroups']:
                all_asg_info['AutoScalingGroupName'] = i['AutoScalingGroupName']
                all_asg_info['AvailabilityZones'] = i['AvailabilityZones']
                all_asg_info['DesiredCapacity'] = i['DesiredCapacity']
                all_asg_info['MaxSize'] = i['MaxSize']
                all_asg_info['MinSize'] = i['MinSize']
                all_asg_info['NewInstancesProtectedFromScaleIn'] = i['NewInstancesProtectedFromScaleIn']
                all_asg_info['Instances'] = []
                for inst in i['Instances']:
                    all_asg_info['Instances'].append({
                        'InstanceId': inst['InstanceId'],
                        'AvailabilityZone': inst['AvailabilityZone'],
                        'HealthStatus': inst['HealthStatus']
                        })
        except Exception as _:
                print('Something went wrong when trying to parse Autoscaling Group information.')
                sys.exit(0)
    
    return all_asg_info

def get_ec2_instance_info(env_resources_ec2_instance_chunk):
    boto3_ec2 = session.client('ec2')
    all_ec2_info = []

    for inst in env_resources_ec2_instance_chunk:
        try:
            inst_info = boto3_ec2.describe_instances(InstanceIds=[inst['Id']])
        except Exception as _:
            print('Something went wrong when trying to get EC2 instance information.')
            sys.exit(0)
        try:
            for i in inst_info['Reservations'][0]['Instances']:
                instance = {}
                instance['InstanceId'] = i['InstanceId']
                instance['InstanceType'] = i['InstanceType']
                instance['ImageId'] = i['ImageId']
                instance['PlatformDetails'] = i['PlatformDetails']
                instance['AvailabilityZone'] = i['Placement']['AvailabilityZone']
                instance['InstanceRole'] = i['IamInstanceProfile']['Arn']
                instance['Monitoring'] = i['Monitoring']['State']
                instance['NetworkInterfaces'] = []
                
                for ni in i['NetworkInterfaces']:
                    netint_json = {}
                    netint_json['PrivateIPAddress'] = ni['PrivateIpAddress']
                    netint_json['PrivateDnsName'] = ni['PrivateDnsName']
                    netint_json['PublicIpAddress'] = ni['Association']['PublicIp']
                    netint_json['PublicDnsName'] = ni['Association']['PublicDnsName']
                    netint_json['MacAddress'] = ni['MacAddress']
                    netint_json['IPv6Address'] = ni['Ipv6Addresses']
                    instance['NetworkInterfaces'].append(netint_json)

                instance['SecurityGroups'] = []
                for sg in i['SecurityGroups']:
                    instance['SecurityGroups'].append(get_security_group_info(sg['GroupId']))
                all_ec2_info.append(instance)

        except Exception as _:
            print('Something went wrong when trying to parse EC2 instance information.')
            sys.exit(0)
    
    return all_ec2_info

def get_security_group_info(security_group_id):
    boto3_ec2 = session.client('ec2')
    
    try:
        sg_info = boto3_ec2.describe_security_groups(GroupIds=[security_group_id])
    except Exception as _:
        print('Something went wrong when trying to get security groups.')
        sys.exit(0)

    try:
        sg = {}
        for i in sg_info['SecurityGroups']:
            sg['GroupId'] = i['GroupId']
            sg['Description'] = i['Description']
            sg['InboundRules'] = []
            sg['OutboundRules'] = []
            
            for rule in i['IpPermissions']:
                rule_json = {}
                if rule['IpProtocol'] != '-1':
                    rule_json['IpProtocol'] = rule['IpProtocol']
                    rule_json['ToPort'] =  rule['ToPort']
                else:
                    rule_json['IpProtocol'] = 'ALL TRAFFIC'
                    rule_json['ToPort'] =  'ALL PORTS'
                
                if len(rule['IpRanges']) != 0:
                    rule_json['From'] = rule['IpRanges'][0]['CidrIp']
                else:
                    rule_json['From'] = rule['UserIdGroupPairs'][0]['GroupId']
                
                sg['InboundRules'].append(rule_json)

            for rule in i['IpPermissionsEgress']:
                rule_json = {}
                if rule['IpProtocol'] != '-1':
                    rule_json['IpProtocol'] = rule['IpProtocol']
                    rule_json['ToPort'] =  rule['ToPort']
                else:
                    rule_json['IpProtocol'] = 'ALL TRAFFIC'
                    rule_json['ToPort'] =  'ALL PORTS'
                
                if len(rule['IpRanges']) != 0:
                    rule_json['To'] = rule['IpRanges'][0]['CidrIp']
                else:
                    rule_json['To'] = rule['UserIdGroupPairs'][0]['GroupId']
                
                sg['OutboundRules'].append(rule_json)
       
    except Exception as _:
        print('Something went wrong when trying to parse security groups.')
        sys.exit(0)
        
    return sg

if __name__ == '__main__':
    argparser = argparse.ArgumentParser(description='Beanstalk Reporter')
    argparser.add_argument('--profile', '-p', metavar='<profile_name>', type=str, help='AWS CLI Profile Name', required=True)
    argparser.add_argument('--envname', '-e', metavar='<env_name>', type=str, help='Beanstalk Environment Name', required=True)
    args = argparser.parse_args()
   
    try:
        session = boto3.session.Session(profile_name = args.profile)
    except Exception as _:
        print('Something went wrong when trying to create a boto3 session. Check your profile.')
        sys.exit(0)

    resources = get_resource_info(environment_name=args.envname)
    print(json.dumps(resources, indent=4, sort_keys=False))
        
    sys.exit(0)