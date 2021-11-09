# Beanstalk-Reporter

Security control auditing on Beanstalk deployments involves the cumbersome proces of manually going through deployment linked resources via the AWS console or CLI, filtering via ARN/ID and having to parse through multiple UI flows and highly verbose API responses respectively (not all of which may be relevant to security engineers) in order to verify configuration.

This tool is written with the intent of simplifying that process. It enumerates resources linked to AWS Elastic Beanstalk deployments including:
- Load Balancers
- Autoscaling Groups
- EC2 instances

It then fetches configuration items for each of the above and filters in information relevant to security controls in a standardized JSON structure. 

You may refer to **[this blog post][0]** for a bit more depth.

## Usage
```
python3 beanstalk_reporter.py --profile <aws_cli_profile_name> --env <beanstalk_env_name>
```

## Demo:
![DemoGIF][1]


## Sample output:
Security-relevant fields for linked components are presented in the structure below. Responses from APIs such as `ec2:describe_*` and `autoscaling:describe_*` contain a much larger amount of information, which may not neccessarily be in the scope of security monitoring.
```
{
    "LoadBalancers": {
        "Details": {
            "DNSName": "awseb-AWSEB-1UVPUXSO6KOIE-1718280053.ap-south-1.elb.amazonaws.com",
            "LoadBalancerName": "awseb-AWSEB-1UVPUXSO6KOIE",
            "AvailabilityZones": [
                {
                    "ZoneName": "ap-south-1b",
                    "SubnetId": "subnet-28a3cf64"
                },
                {
                    "ZoneName": "ap-south-1a",
                    "SubnetId": "subnet-7ba79813"
                }
            ],
            "SecurityGroups": [
                "sg-0306ad9cbb3900202"
            ],
            "VpcId": "vpc-c0adbba8"
        },
        "Attributes": {
            "access_logs.s3.enabled": "false",
            "access_logs.s3.bucket": "",
            "access_logs.s3.prefix": "",
            "idle_timeout.timeout_seconds": "60",
            "deletion_protection.enabled": "false",
            "routing.http2.enabled": "true",
            "routing.http.drop_invalid_header_fields.enabled": "false",
            "routing.http.xff_client_port.enabled": "false",
            "routing.http.desync_mitigation_mode": "defensive",
            "waf.fail_open.enabled": "false",
            "routing.http.x_amzn_tls_version_and_cipher_suite.enabled": "false"
        },
        "Listeners": [
            {
                "Protocol": "HTTP",
                "Port": 80,
                "TargetGroupStickiness": false
            }
        ],
        "SecurityGroups": [
            {
                "GroupId": "sg-0306ad9cbb3900202",
                "Description": "Load Balancer Security Group",
                "InboundRules": [
                    {
                        "IpProtocol": "tcp",
                        "ToPort": 80,
                        "From": "0.0.0.0/0"
                    }
                ],
                "OutboundRules": [
                    {
                        "IpProtocol": "tcp",
                        "ToPort": 80,
                        "To": "0.0.0.0/0"
                    }
                ]
            }
        ]
    },
    "AutoScalingGroups": {
        "AutoScalingGroupName": "awseb-e-nqr3wfc2ss-stack-AWSEBAutoScalingGroup-1EWYSNAEDH40D",
        "AvailabilityZones": [
            "ap-south-1b",
            "ap-south-1a"
        ],
        "DesiredCapacity": 2,
        "MaxSize": 2,
        "MinSize": 2,
        "NewInstancesProtectedFromScaleIn": false,
        "Instances": [
            {
                "InstanceId": "i-00431322e2b12a257",
                "AvailabilityZone": "ap-south-1b",
                "HealthStatus": "Healthy"
            },
            {
                "InstanceId": "i-0dc3bbfd97c783eb6",
                "AvailabilityZone": "ap-south-1a",
                "HealthStatus": "Healthy"
            }
        ]
    },
    "Instances": [
        {
            "InstanceId": "i-00431322e2b12a257",
            "InstanceType": "t2.micro",
            "ImageId": "ami-0e932ae268855ee62",
            "PlatformDetails": "Linux/UNIX",
            "AvailabilityZone": "ap-south-1b",
            "InstanceRole": "arn:aws:iam::153316549657:instance-profile/aws-elasticbeanstalk-ec2-role",
            "Monitoring": "disabled",
            "NetworkInterfaces": [
                {
                    "PrivateIPAddress": "172.31.2.132",
                    "PrivateDnsName": "ip-172-31-2-132.ap-south-1.compute.internal",
                    "PublicIpAddress": "15.207.110.197",
                    "PublicDnsName": "ec2-15-207-110-197.ap-south-1.compute.amazonaws.com",
                    "MacAddress": "0a:09:71:b7:3b:2a",
                    "IPv6Address": []
                }
            ],
            "SecurityGroups": [
                {
                    "GroupId": "sg-080a3f187c29db02a",
                    "Description": "VPC Security Group",
                    "InboundRules": [
                        {
                            "IpProtocol": "tcp",
                            "ToPort": 80,
                            "From": "sg-0306ad9cbb3900202"
                        }
                    ],
                    "OutboundRules": [
                        {
                            "IpProtocol": "ALL TRAFFIC",
                            "ToPort": "ALL PORTS",
                            "To": "0.0.0.0/0"
                        }
                    ]
                }
            ]
        },
        {
            "InstanceId": "i-0dc3bbfd97c783eb6",
            "InstanceType": "t2.micro",
            "ImageId": "ami-0e932ae268855ee62",
            "PlatformDetails": "Linux/UNIX",
            "AvailabilityZone": "ap-south-1a",
            "InstanceRole": "arn:aws:iam::153316549657:instance-profile/aws-elasticbeanstalk-ec2-role",
            "Monitoring": "disabled",
            "NetworkInterfaces": [
                {
                    "PrivateIPAddress": "172.31.39.85",
                    "PrivateDnsName": "ip-172-31-39-85.ap-south-1.compute.internal",
                    "PublicIpAddress": "65.0.85.185",
                    "PublicDnsName": "ec2-65-0-85-185.ap-south-1.compute.amazonaws.com",
                    "MacAddress": "02:e3:eb:e7:16:c8",
                    "IPv6Address": []
                }
            ],
            "SecurityGroups": [
                {
                    "GroupId": "sg-080a3f187c29db02a",
                    "Description": "VPC Security Group",
                    "InboundRules": [
                        {
                            "IpProtocol": "tcp",
                            "ToPort": 80,
                            "From": "sg-0306ad9cbb3900202"
                        }
                    ],
                    "OutboundRules": [
                        {
                            "IpProtocol": "ALL TRAFFIC",
                            "ToPort": "ALL PORTS",
                            "To": "0.0.0.0/0"
                        }
                    ]
                }
            ]
        }
    ]
}
```

[0]: https://www.anishsujanani.me/2021/11/08/beanstalk-reporter.html
[1]: https://github.com/anishsujanani/Beanstalk-Reporter/blob/master/opgif.gif
