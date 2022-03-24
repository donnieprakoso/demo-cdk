import aws_cdk as core
import aws_cdk.assertions as assertions

from 6_cdk_pipelines.6_cdk_pipelines_stack import 6CdkPipelinesStack

# example tests. To run these tests, uncomment this file along with the example
# resource in 6_cdk_pipelines/6_cdk_pipelines_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = 6CdkPipelinesStack(app, "6-cdk-pipelines")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
