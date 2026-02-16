# AWS IAM Policy Requirements for GitHub Actions Deploy

The IAM user `github-aws-ses-contact-form-chrispivonka.com` needs the following permissions to deploy via GitHub Actions.

## Required IAM Policy

Replace `995772609444` with your actual AWS account ID and `us-east-1` with your region.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "CloudFormationAccess",
      "Effect": "Allow",
      "Action": [
        "cloudformation:CreateChangeSet",
        "cloudformation:DescribeChangeSet",
        "cloudformation:ExecuteChangeSet",
        "cloudformation:DescribeStacks",
        "cloudformation:GetTemplate",
        "cloudformation:UpdateStack"
      ],
      "Resource": "arn:aws:cloudformation:us-east-1:995772609444:stack/contact-form-handler-*"
    },
    {
      "Sid": "CloudFormationTransform",
      "Effect": "Allow",
      "Action": [
        "cloudformation:CreateChangeSet"
      ],
      "Resource": "arn:aws:cloudformation:us-east-1:aws:transform/Serverless-2016-10-31"
    },
    {
      "Sid": "S3Access",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:GetObjectVersion"
      ],
      "Resource": "arn:aws:s3:::*"
    },
    {
      "Sid": "LambdaAccess",
      "Effect": "Allow",
      "Action": [
        "lambda:CreateFunction",
        "lambda:UpdateFunctionCode",
        "lambda:UpdateFunctionConfiguration",
        "lambda:GetFunction",
        "lambda:AddPermission",
        "lambda:RemovePermission"
      ],
      "Resource": "arn:aws:lambda:us-east-1:995772609444:function/contact-form-handler*"
    },
    {
      "Sid": "APIGatewayAccess",
      "Effect": "Allow",
      "Action": [
        "apigateway:POST",
        "apigateway:DELETE",
        "apigateway:PUT",
        "apigateway:PATCH",
        "apigateway:GET"
      ],
      "Resource": "arn:aws:apigateway:us-east-1::*"
    },
    {
      "Sid": "IAMRoleAccess",
      "Effect": "Allow",
      "Action": [
        "iam:CreateRole",
        "iam:DeleteRole",
        "iam:GetRole",
        "iam:PassRole",
        "iam:PutRolePolicy",
        "iam:DeleteRolePolicy",
        "iam:AttachRolePolicy",
        "iam:DetachRolePolicy",
        "iam:GetRolePolicy",
        "iam:ListRolePolicies"
      ],
      "Resource": "arn:aws:iam::995772609444:role/contact-form-handler*"
    },
    {
      "Sid": "CloudWatchLogs",
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:DeleteLogGroup",
        "logs:DescribeLogGroups"
      ],
      "Resource": "arn:aws:logs:us-east-1:995772609444:log-group:/aws/lambda/contact-form-handler*"
    },
    {
      "Sid": "SESPermissions",
      "Effect": "Allow",
      "Action": [
        "ses:SendEmail"
      ],
      "Resource": "arn:aws:ses:us-east-1:995772609444:identity/website-contact@chrispivonka.com"
    }
  ]
}
```

## Steps to Apply

1. Go to [AWS IAM Users](https://console.aws.amazon.com/iam/home#/users)
2. Find user: `github-aws-ses-contact-form-chrispivonka.com`
3. Click **Add inline policy** (or update existing policy)
4. Paste the JSON policy above
5. Verify the policy is attached

## Deployment Troubleshooting

If you still get `CreateChangeSet` errors:
- Verify the user has the exact permissions listed above
- Check that you attached the policy to the correct IAM user
- Ensure the resource ARNs match your AWS account ID (995772609444)
- Try running `sam deploy` locally first to verify permissions work
