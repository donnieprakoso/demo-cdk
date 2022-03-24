#!/usr/bin/env python
from constructs import Construct
from cdktf import App, TerraformStack
from imports.aws import AwsProvider
from imports.AwsLambda import AwsLambda

class MyStack(TerraformStack):
    def __init__(self, scope: Construct, ns: str):
        super().__init__(scope, ns)

        # define resources here
        AwsProvider(self, "Aws", region="ap-southeast-1")
        fn_lambda = AwsLambda(self, "cdktf-lambda",
            create = True,
            handler = "app.handler",
            runtime="python3.8",
            function_name="cdktf-lambda",
            source_path = "/data/codes/demo-cdk/3-cdktf/cdk/lambda-function/"

        )


app = App()
MyStack(app, "cdk")

app.synth()
