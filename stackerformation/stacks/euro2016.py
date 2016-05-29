from troposphere import Ref, Base64, Join
from troposphere.iam import Role, PolicyProperty, InstanceProfile
from troposphere.autoscaling import Tag
from troposphere.autoscaling import AutoScalingGroup
from troposphere.autoscaling import LaunchConfiguration
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
            "description": "Base AMI to use for prediction_service"
        },
        "InstanceType": {
            "type": "String",
            "description": "EC2 instance size to use for prediction_service"
        },
        "AppVersion": {
            "type": "String",
            "description": "Version of prediction service"
        }
    }

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
            self, prediction_service_instance_profile
    ):
        t = self.template

        prediction_service_launch_configuration = t.add_resource(
            LaunchConfiguration(
                "Euro2016LaunchConfiguration",
                UserData=Base64(Join("", [
                    "#!/bin/bash -ex\n",
                    "yum clean all\n",
                    "yum update -y\n",
                    "mkdir -p /opt/euro2016\n",
                    "aws s3 cp s3://oliviervg1-code/euro2016/app-", Ref("AppVersion"), ".zip /tmp/app.zip\n",  # noqa
                    "unzip /tmp/app.zip -d /opt/euro2016/\n",
                    "cd /opt/euro2016\n",
                    "pip install --no-index --find-links pip-repo/ -r requirements.txt\n",  # noqa
                    "cd src\n",
                    "gunicorn app:app &"
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
                Tag("Name", "euro2016-prediction-service", True),
            ],
            LaunchConfigurationName=Ref(
                prediction_service_launch_configuration
            ),
            MinSize="1",
            MaxSize="1",
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
        instance_profile = self.create_prediction_service_instance_profile()
        self.create_prediction_service_autoscaling_group(instance_profile)
