#!/usr/bin/env python3

from constructs import Construct
from aws_cdk import App, Stack, Stage
import os
from aws_cdk import aws_dynamodb as dynamodb
from aws_cdk import pipelines
from aws_cdk import aws_lambda as _lambda
import aws_cdk as _cdk


class LambdaFunctionStack(Stack):
    def __init__(self, scope, id):
        super().__init__(scope, id)
        fn_lambda_a = _lambda.Function(
            self,
            "{}-function-".format(id),
            code=_lambda.AssetCode("../lambda-function/"),
            handler="app.handler",
            timeout=_cdk.Duration.seconds(60),
            runtime=_lambda.Runtime.PYTHON_3_8)


class PipelineStack(Stack):
    def __init__(self, scope, id, env=None):
        super().__init__(scope, id, env=env)

        pipeline = pipelines.CodePipeline(
            self,
            "Pipeline",
            synth=pipelines.ShellStep(
                "Synth",
                input=pipelines.CodePipelineSource.connection(
                    "donnieprakoso/demo-cdk",
                    "main",
                    connection_arn="arn:aws:codestar-connections:ap-southeast-1:194989662172:connection/55046ac9-4dd4-41a1-a3f8-e1bba5b20cff"
                ),
                commands=["cd 5-cdk-pipelines/cdk/", "npm install -g aws-cdk",
                          "pip install -r requirements.txt", "cdk synth"],
                primary_output_directory="5-cdk-pipelines/cdk/cdk.out"
            ))

        pipeline.add_stage(
            DemoApplication(self,
                            "staging",
                            env=env))


class DemoApplication(Stage):
    def __init__(self, scope, id, *, env=None):
        super().__init__(scope, id, env=env)

        LambdaFunctionStack(self, "lambda")


AWS_ACCOUNT_ID = _cdk.Aws.ACCOUNT_ID
AWS_REGION = _cdk.Aws.REGION
STACK_NAME = "democdk-lambda"

app = _cdk.App()
pipeline = PipelineStack(
    app,
    "{}-pipeline".format(STACK_NAME),
    env=_cdk.Environment(account=AWS_ACCOUNT_ID, region=AWS_REGION),
)

app.synth()
