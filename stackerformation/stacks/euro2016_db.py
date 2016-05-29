from troposphere import GetAtt, Output, Ref
from troposphere.ec2 import Tag
from troposphere.rds import DBInstance, DBSubnetGroup


from stacker.blueprints.base import Blueprint


class PredictionServiceDB(Blueprint):

    PARAMETERS = {
        "DBSubnetIds": {
            "type": "CommaDelimitedList",
            "description": "List of DB subnet ids"
        },
        "DBSecurityGroups": {
            "type": "CommaDelimitedList",
            "description": "List of DB security groups"
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
        "DBInstanceClass": {
            "type": "String",
            "description": "DB class"
        },
        "DBSize": {
            "type": "Number",
            "description": "DB size (Gb)"
        }
    }

    def create_prediction_service_db_subnet_group(self):
        t = self.template

        return t.add_resource(DBSubnetGroup(
            "Euro2016DBSubnetGroup",
            DBSubnetGroupDescription="Subnets available for the DB instance",
            SubnetIds=Ref("DBSubnetIds"),
        ))

    def create_prediction_service_db(self, subnet_group):
        t = self.template

        t.add_resource(DBInstance(
            "Euro2016DB",
            DBName=Ref("DBName"),
            AllocatedStorage=Ref("DBSize"),
            DBInstanceClass=Ref("DBInstanceClass"),
            Engine="MySQL",
            EngineVersion="5.7",
            MasterUsername=Ref("DBUser"),
            MasterUserPassword=Ref("DBPassword"),
            DBSubnetGroupName=Ref(subnet_group),
            VPCSecurityGroups=Ref("DBSecurityGroups"),
            MultiAZ=True,
            StorageType="gp2",
            Tags=[Tag("Name", "euro2016-prediction-db")]
        ))

        t.add_output(Output(
            "DBAddress",
            Description="Database address",
            Value=GetAtt("Euro2016DB", "Endpoint.Address")
        ))

        t.add_output(Output(
            "DBPort",
            Description="Database port",
            Value=GetAtt("Euro2016DB", "Endpoint.Port")
        ))

    def create_template(self):
        subnet_group = self.create_prediction_service_db_subnet_group()
        self.create_prediction_service_db(subnet_group)
