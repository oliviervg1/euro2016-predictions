from troposphere import Ref, Base64, Join
from troposphere.iam import Role, PolicyProperty, InstanceProfile
from troposphere.ec2 import Tag
from troposphere.autoscaling import Tag as AsgTag
from troposphere.autoscaling import AutoScalingGroup
from troposphere.autoscaling import LaunchConfiguration
from troposphere.elasticloadbalancing import LoadBalancer, HealthCheck
from troposphere.policies import UpdatePolicy, AutoScalingRollingUpdate

from awacs.aws import Policy, Statement, Principal, Action

from stacker.blueprints.base import Blueprint


class PredictionService(Blueprint):

    PARAMETERS = {
        "ELBSubnetIds": {
            "type": "CommaDelimitedList",
            "description": "List of ELB subnet ids"
        },
        "ELBSecurityGroups": {
            "type": "CommaDelimitedList",
            "description": "List of ELB security groups"
        },
        "EC2SubnetIds": {
            "type": "CommaDelimitedList",
            "description": "List of EC2 subnet ids"
        },
        "EC2SecurityGroups": {
            "type": "CommaDelimitedList",
            "description": "List of EC2 security groups"
        },
        "KeyName": {
            "type": "String",
            "description": "Key name to use for SSH"
        },
        "BaseAMI": {
            "type": "String",
            "description": "Base AMI to use for prediction service"
        },
        "InstanceType": {
            "type": "String",
            "description": "EC2 instance size to use for prediction service"
        },
        "DomainName": {
            "type": "String",
            "description": "The domain name the app is running on"
        },
        "WhitelistedEmailDomains": {
            "type": "String",
            "description": (
                "Comma delimited list of emails domains that are allowed to "
                "sign in"
            )
        },
        "SSLCertificateId": {
            "type": "String",
            "description": "The ARN of the SSL certificate to use"
        },
        "AppVersion": {
            "type": "String",
            "description": "Version of prediction service"
        },
        "DBName": {
            "type": "String",
            "description": "DB name"
        },
        "DBUser": {
            "type": "String",
            "description": "DB user"
        },
        "DBPassword": {
            "type": "String",
            "description": "DB password",
            "no_echo": True
        },
        "DBAddress": {
            "type": "String",
            "description": "DB address"
        },
        "DBPort": {
            "type": "String",
            "description": "DB port"
        }
    }

    def create_prediction_service_elb(self):
        t = self.template

        prediction_service_elastic_load_balancer = t.add_resource(LoadBalancer(
            "Euro2016ElasticLoadBalancer",
            LoadBalancerName="euro2016-prediction-service-elb",
            Subnets=Ref("ELBSubnetIds"),
            Listeners=[
                {
                    "InstancePort": "8000",
                    "LoadBalancerPort": "80",
                    "Protocol": "HTTP"
                },
                {
                    "InstancePort": "8000",
                    "LoadBalancerPort": "443",
                    "Protocol": "HTTPS",
                    "SSLCertificateId": Ref("SSLCertificateId")
                }
            ],
            SecurityGroups=Ref("ELBSecurityGroups"),
            HealthCheck=HealthCheck(
                HealthyThreshold="3",
                Interval="30",
                Target="HTTP:8000/status",
                Timeout="5",
                UnhealthyThreshold="5",
            ),
            CrossZone=True,
            Tags=[Tag("Name", "euro2016-prediction-service-elb")]
        ))

        return prediction_service_elastic_load_balancer

    def create_prediction_service_instance_profile(self):
        t = self.template

        prediction_service_iam_policy = PolicyProperty(
            PolicyName="euro2016-prediction-service-policy",
            PolicyDocument=Policy(
                Statement=[
                    Statement(
                        Effect="Allow",
                        Action=[Action("s3", "ListBucket")],
                        Resource=["arn:aws:s3:::oliviervg1-code"]
                    ),
                    Statement(
                        Effect="Allow",
                        Action=[Action("s3", "GetObject")],
                        Resource=["arn:aws:s3:::oliviervg1-code/euro2016/*"]
                    )
                ]
            )
        )

        prediction_service_iam_role = t.add_resource(Role(
            "Euro2016IamRole",
            AssumeRolePolicyDocument=Policy(
                Statement=[Statement(
                    Effect="Allow",
                    Principal=Principal(
                        "Service", ["ec2.amazonaws.com"]
                    ),
                    Action=[Action("sts", "AssumeRole")]
                )]
            ),
            Policies=[prediction_service_iam_policy],
            Path="/"
        ))

        prediction_service_instance_profile = t.add_resource(InstanceProfile(
            "Euro2016InstanceProfile",
            Roles=[Ref(prediction_service_iam_role)],
            Path="/"
        ))

        return prediction_service_instance_profile

    def create_prediction_service_autoscaling_group(
            self, prediction_service_elb, prediction_service_instance_profile
    ):
        t = self.template

        prediction_service_launch_configuration = t.add_resource(
            LaunchConfiguration(
                "Euro2016LaunchConfiguration",
                UserData=Base64(Join("", [
                    "#!/bin/bash -ex\n",

                    "# Update system\n",
                    "yum clean all\n",
                    "yum update -y\n",

                    "# Fetch application\n",
                    "mkdir -p /opt/euro2016\n",
                    "aws s3 cp s3://oliviervg1-code/euro2016/app-", Ref("AppVersion"), ".zip /tmp/app.zip\n",  # noqa
                    "unzip /tmp/app.zip -d /opt/euro2016/\n",

                    "# Install dependencies\n",
                    "cd /opt/euro2016\n",
                    "yum install -y nginx gcc mysql-devel\n",
                    "pip install --no-index --find-links pip-repo/ -r requirements.txt --upgrade\n",  # noqa
                    "sed -i.bak -e 's|CHANGE_ME_DOMAIN_NAME|", Ref("DomainName"), "|' config/nginx.conf\n"  # noqa
                    "cp config/nginx.conf /etc/nginx/nginx.conf\n",
                    "service nginx restart\n",

                    "# Update config\n",
                    "sed -i.bak -e 's|_all_|", Ref("WhitelistedEmailDomains"), "|' -e 's|sqlite:///euro2016.db|mysql://", Ref("DBUser"), ":", Ref("DBPassword"), "@", Ref("DBAddress"), ":", Ref("DBPort"), "/", Ref("DBName"), "|' config/config.cfg\n",  # noqa

                    "# Create db tables\n",
                    "python create_db_tables.py\n",

                    "# Start application\n",
                    "/usr/local/bin/gunicorn -c config/gunicorn.py app:app"
                ])),
                ImageId=Ref("BaseAMI"),
                KeyName=Ref("KeyName"),
                SecurityGroups=Ref("EC2SecurityGroups"),
                InstanceType=Ref("InstanceType"),
                IamInstanceProfile=Ref(prediction_service_instance_profile),
                AssociatePublicIpAddress="true",
            )
        )

        t.add_resource(AutoScalingGroup(
            "Euro2016AutoscalingGroup",
            Tags=[
                AsgTag("Name", "euro2016-prediction-service", True),
            ],
            LaunchConfigurationName=Ref(
                prediction_service_launch_configuration
            ),
            MinSize="1",
            MaxSize="1",
            LoadBalancerNames=[Ref(prediction_service_elb)],
            VPCZoneIdentifier=Ref("EC2SubnetIds"),
            UpdatePolicy=UpdatePolicy(
                AutoScalingRollingUpdate=AutoScalingRollingUpdate(
                    PauseTime="PT0S",
                    MinInstancesInService="0",
                    MaxBatchSize="1"
                )
            )
        ))

    def create_template(self):
        elb = self.create_prediction_service_elb()
        instance_profile = self.create_prediction_service_instance_profile()
        self.create_prediction_service_autoscaling_group(elb, instance_profile)
