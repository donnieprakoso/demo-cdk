from constructs import Construct
import aws_cdk as _cdk
from aws_cdk import (
    App, Stack,
    aws_lambda as _lambda
)


class LambdaFunction(Stack):

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        fn_lambda = _lambda.Function(
            self,
            "{}-function-a".format(id),
            code=_lambda.AssetCode("../lambda-functions/function-hello"),
            handler="app.handler",
            timeout=_cdk.Duration.seconds(60),
            runtime=_lambda.Runtime.PYTHON_3_8)


app = App()
LambdaFunction(app, "cdk-lambda-multiple-env-staging")

app.synth()
