#!/usr/bin/env python3

from constructs import Construct
from aws_cdk import App, Stack, Stage
import os
from aws_cdk import aws_iam as _iam
from aws_cdk import aws_dynamodb as _ddb
from aws_cdk import aws_lambda as _lambda
import aws_cdk as _cdk
from aws_cdk import aws_ssm as _ssm
from aws_cdk import aws_apigateway as _ag
from aws_cdk import pipelines


class ServerlessApiStack(Stack):
    def __init__(self, scope, id):
        super().__init__(scope, id)
        # Model all required resources
        ddb_table = _ddb.Table(
            self,
            id='{}-data'.format(id),
            table_name='{}-data'.format(id),
            partition_key=_ddb.Attribute(name='ID',
                                         type=_ddb.AttributeType.STRING),
            removal_policy=_cdk.RemovalPolicy.
            DESTROY,  # THIS IS NOT RECOMMENDED FOR PRODUCTION USE
            read_capacity=1,
            write_capacity=1)

        # IAM Roles
        lambda_role = _iam.Role(
            self,
            id='{}-lambda-role'.format(id),
            assumed_by=_iam.ServicePrincipal('lambda.amazonaws.com'))

        cw_policy_statement = _iam.PolicyStatement(effect=_iam.Effect.ALLOW)
        cw_policy_statement.add_actions("logs:CreateLogGroup")
        cw_policy_statement.add_actions("logs:CreateLogStream")
        cw_policy_statement.add_actions("logs:PutLogEvents")
        cw_policy_statement.add_actions("logs:DescribeLogStreams")
        cw_policy_statement.add_resources("*")
        lambda_role.add_to_policy(cw_policy_statement)

        # Add role for DynamoDB
        dynamodb_policy_statement = _iam.PolicyStatement(
            effect=_iam.Effect.ALLOW)
        dynamodb_policy_statement.add_actions("dynamodb:PutItem")
        dynamodb_policy_statement.add_actions("dynamodb:GetItem")
        dynamodb_policy_statement.add_actions("dynamodb:UpdateItem")
        dynamodb_policy_statement.add_actions("dynamodb:DeleteItem")
        dynamodb_policy_statement.add_actions("dynamodb:Scan")
        dynamodb_policy_statement.add_actions("dynamodb:Query")
        dynamodb_policy_statement.add_actions("dynamodb:ConditionCheckItem")
        dynamodb_policy_statement.add_resources(ddb_table.table_arn)
        lambda_role.add_to_policy(dynamodb_policy_statement)

        # AWS Lambda Functions
        fnLambda_saveData = _lambda.Function(
            self,
            "{}-function-saveData".format(id),
            code=_lambda.AssetCode("../lambda-functions/save-data"),
            handler="app.handler",
            timeout=_cdk.Duration.seconds(60),
            role=lambda_role,
            tracing=_lambda.Tracing.ACTIVE,
            runtime=_lambda.Runtime.PYTHON_3_8)
        fnLambda_saveData.add_environment("TABLE_NAME", ddb_table.table_name)

        fnLambda_listData = _lambda.Function(
            self,
            "{}-function-listData".format(id),
            code=_lambda.AssetCode("../lambda-functions/list-data"),
            handler="app.handler",
            timeout=_cdk.Duration.seconds(60),
            role=lambda_role,
            tracing=_lambda.Tracing.ACTIVE,
            runtime=_lambda.Runtime.PYTHON_3_8)
        fnLambda_listData.add_environment("TABLE_NAME", ddb_table.table_name)

        fnLambda_getData = _lambda.Function(
            self,
            "{}-function-getData".format(id),
            code=_lambda.AssetCode("../lambda-functions/get-data"),
            handler="app.handler",
            timeout=_cdk.Duration.seconds(60),
            role=lambda_role,
            tracing=_lambda.Tracing.ACTIVE,
            runtime=_lambda.Runtime.PYTHON_3_8)
        fnLambda_getData.add_environment("TABLE_NAME", ddb_table.table_name)

        fnLambda_deleteData = _lambda.Function(
            self,
            "{}-function-deleteData".format(id),
            code=_lambda.AssetCode("../lambda-functions/delete-data"),
            handler="app.handler",
            timeout=_cdk.Duration.seconds(60),
            role=lambda_role,
            tracing=_lambda.Tracing.ACTIVE,
            runtime=_lambda.Runtime.PYTHON_3_8)
        fnLambda_deleteData.add_environment("TABLE_NAME", ddb_table.table_name)

        api = _ag.RestApi(
            self,
            id="{}-api-gateway".format(id),
        )

        int_saveData = _ag.LambdaIntegration(fnLambda_saveData)
        int_listData = _ag.LambdaIntegration(fnLambda_listData)
        int_getData = _ag.LambdaIntegration(fnLambda_getData)
        int_deleteData = _ag.LambdaIntegration(fnLambda_deleteData)

        res_data = api.root.add_resource('data')
        res_data.add_method('POST', int_saveData)
        res_data.add_method('GET', int_listData)

        res_data_id = res_data.add_resource('{id}')
        res_data_id.add_method('GET', int_getData)
        res_data_id.add_method('DELETE', int_deleteData)

        self.out_dynamodb = _cdk.CfnOutput(self,
                                           "{}-output-dynamodbTable".format(
                                               id),
                                           value=ddb_table.table_name,
                                           export_name="{}-ddbTable".format(id))

        self.out_apiendpointURL = _cdk.CfnOutput(self,
                                                 "{}-output-apiEndpointURL".format(
                                                     id),
                                                 value=api.url,
                                                 export_name="{}-apiEndpointURL".format(id))


class PipelineStack(Stack):
    def __init__(self, scope, id, env=None):
        super().__init__(scope, id, env=env)

        github_connection_arn = _ssm.StringParameter.from_string_parameter_name(
            self,
            "github-connection-arn",
            string_parameter_name="github-connection-arn").string_value
        pipeline = pipelines.CodePipeline(
            self,
            "Pipeline",
            synth=pipelines.ShellStep(
                "Synth",
                input=pipelines.CodePipelineSource.connection(
                    "donnieprakoso/demo-cdk",
                    "main",
                    connection_arn=github_connection_arn),
                commands=[
                    "cd 6-pipelines-serverless-api/cdk/",
                    "npm install -g aws-cdk",
                    "pip install -r requirements.txt", "cdk synth"
                ],
                primary_output_directory="6-pipelines-serverless-api/cdk/cdk.out"))

        staging_app = DemoApplication(self, "staging", env=env)

        # Use case 1: Deployment to staging
        # pipeline.add_stage(staging_app)

        # Use case 2: Deployment to staging with integration testing
        pipeline.add_stage(staging_app, post=[
            pipelines.ShellStep("Integration Test",
                                commands=[
                                    'curl $ENDPOINT_URL/data',
                                ],
                                env_from_cfn_outputs={
                                    "ENDPOINT_URL": staging_app.out_apiendpointURL}
                                )
        ])

        # Use case 3: Deployment to multiple environment (production) with manual approval
        # production_app = DemoApplication(self, "production", env=env)
        # pipeline.add_stage(production_app,
        #                    pre=[pipelines.ManualApprovalStep("DeployToProduction")])


class DemoApplication(Stage):
    def __init__(self, scope, id, *, env=None):
        super().__init__(scope, id, env=env)
        app = ServerlessApiStack(self, "{}-api".format(id))
        self.out_apiendpointURL = app.out_apiendpointURL


AWS_ACCOUNT_ID = _cdk.Aws.ACCOUNT_ID
AWS_REGION = _cdk.Aws.REGION
STACK_NAME = "democdkpipelines-api"

app = _cdk.App()
pipeline = PipelineStack(
    app,
    "{}-pipeline".format(STACK_NAME),
    env=_cdk.Environment(account=AWS_ACCOUNT_ID, region=AWS_REGION),
)

app.synth()
