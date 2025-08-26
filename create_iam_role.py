#!/usr/bin/env python3
"""
IAMロール作成スクリプト（Code Interpreter用）
"""

import boto3
import json
import time
from botocore.exceptions import ClientError

# AWSクライアント
iam = boto3.client('iam')
sts = boto3.client('sts')

def get_account_id():
    """AWSアカウントIDを取得"""
    return sts.get_caller_identity()["Account"]

def create_trust_policy(account_id):
    """信頼ポリシーを生成（Runtime用）"""
    return {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "bedrock-agentcore.amazonaws.com"
                },
                "Action": "sts:AssumeRole",
                "Condition": {
                    "StringEquals": {
                        "aws:SourceAccount": account_id
                    },
                    "ArnLike": {
                        "aws:SourceArn": f"arn:aws:bedrock-agentcore:us-west-2:{account_id}:*"
                    }
                }
            }
        ]
    }

def create_runtime_policy(account_id):
    """Runtime用の詳細なポリシーを生成"""
    return {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "BedrockModelAccess",
                "Effect": "Allow",
                "Action": [
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream"
                ],
                "Resource": [
                    "arn:aws:bedrock:*::foundation-model/*"
                ]
            },
            {
                "Sid": "CodeInterpreterAccess",
                "Effect": "Allow",
                "Action": [
                    "bedrock-agentcore:CreateCodeInterpreter",
                    "bedrock-agentcore:StartCodeInterpreterSession",
                    "bedrock-agentcore:InvokeCodeInterpreter",
                    "bedrock-agentcore:StopCodeInterpreterSession",
                    "bedrock-agentcore:DeleteCodeInterpreter",
                    "bedrock-agentcore:ListCodeInterpreters",
                    "bedrock-agentcore:GetCodeInterpreter"
                ],
                "Resource": "*"
            },
            {
                "Sid": "LogsDescribeLogGroups",
                "Effect": "Allow",
                "Action": [
                    "logs:DescribeLogGroups"
                ],
                "Resource": "*"
            },
            {
                "Sid": "LogsGroupLevel",
                "Effect": "Allow",
                "Action": [
                    "logs:CreateLogGroup",
                    "logs:DescribeLogStreams"
                ],
                "Resource": [
                    f"arn:aws:logs:us-west-2:{account_id}:log-group:/aws/bedrock-agentcore/runtimes/*"
                ]
            },
            {
                "Sid": "LogsStreamLevel",
                "Effect": "Allow",
                "Action": [
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ],
                "Resource": [
                    f"arn:aws:logs:us-west-2:{account_id}:log-group:/aws/bedrock-agentcore/runtimes/*:log-stream:*"
                ]
            },
            {
                "Sid": "XRayAccess",
                "Effect": "Allow",
                "Action": [
                    "xray:PutTraceSegments",
                    "xray:PutTelemetryRecords",
                    "xray:GetSamplingRules",
                    "xray:GetSamplingTargets"
                ],
                "Resource": ["*"]
            },
            {
                "Sid": "CloudWatchMetrics",
                "Effect": "Allow",
                "Action": "cloudwatch:PutMetricData",
                "Resource": "*",
                "Condition": {
                    "StringEquals": {
                        "cloudwatch:namespace": "bedrock-agentcore"
                    }
                }
            },
            {
                "Sid": "ECRAccess",
                "Effect": "Allow",
                "Action": [
                    "ecr:GetAuthorizationToken",
                    "ecr:BatchGetImage",
                    "ecr:GetDownloadUrlForLayer"
                ],
                "Resource": ["*"]
            },
            {
                "Sid": "S3ListAllBuckets",
                "Effect": "Allow",
                "Action": [
                    "s3:ListAllMyBuckets"
                ],
                "Resource": [
                    "*"
                ]
            },
            {
                "Sid": "S3BucketLevel",
                "Effect": "Allow",
                "Action": [
                    "s3:GetBucketLocation",
                    "s3:ListBucket"
                ],
                "Resource": [
                    "arn:aws:s3:::*"
                ]
            },
            {
                "Sid": "S3ObjectLevel",
                "Effect": "Allow",
                "Action": [
                    "s3:GetObject",
                    "s3:PutObject"
                ],
                "Resource": [
                    "arn:aws:s3:::*/*"
                ]
            }
        ]
    }

def create_iam_role():
    """Runtime用IAMロールを作成"""
    account_id = get_account_id()
    timestamp = int(time.time())
    role_name = f"CodeInterpreterRuntimeRole-{timestamp}"
    
    print(f"🚀 IAMロール作成開始: {role_name}")
    print(f"   アカウントID: {account_id}")
    
    try:
        # 信頼ポリシーの作成
        trust_policy = create_trust_policy(account_id)
        
        # IAMロールの作成
        role_response = iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
        )
        
        role_arn = role_response['Role']['Arn']
        print(f"✅ IAMロール作成成功: {role_name}")
        
        # ポリシーの作成とアタッチ
        policy_name = f"CodeInterpreterRuntimePolicy-{timestamp}"
        runtime_policy = create_runtime_policy(account_id)
        
        policy_response = iam.create_policy(
            PolicyName=policy_name,
            PolicyDocument=json.dumps(runtime_policy)
        )
        
        policy_arn = policy_response['Policy']['Arn']
        
        # ポリシーをロールにアタッチ
        iam.attach_role_policy(
            RoleName=role_name,
            PolicyArn=policy_arn
        )
        
        print(f"✅ ポリシーアタッチ完了: {policy_name}")
        print(f"🎉 Runtime Role ARN: {role_arn}")
        print("\n📝 メモ: このARNをdeploy_runtime.pyのruntime_role_arn変数に設定してください")
        
        return role_arn
        
    except ClientError as e:
        print(f"❌ エラー: {e}")
        raise

if __name__ == "__main__":
    role_arn = create_iam_role()