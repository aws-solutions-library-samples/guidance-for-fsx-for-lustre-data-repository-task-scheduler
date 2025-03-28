# Guidance for FSx for Lustre Data Repository Task Scheduler

## Table of Contents

1. [Overview](#overview)
    - [Cost](#cost)
2. [Prerequisites](#prerequisites)
    - [Operating System](#operating-system)
    - [AWS account requirements](#aws-account-requirements)
3. [Deployment Steps](#deployment-steps)
4. [Deployment Validation](#deployment-validation)
5. [Running the Guidance](#running-the-guidance)
6. [Next Steps](#next-steps)
7. [Cleanup](#cleanup)

## Overview

This Guidance provides a solution for scheduling and automating data repository tasks for Amazon FSx for Lustre file systems. It creates a CloudWatch scheduled event that triggers a Lambda function to execute FSx data repository tasks, allowing for automated import of metadata or export of data between FSx for Lustre and Amazon S3.

The solution works as follows:![Architecture diagram](assets/refarch.png)

1. An AWS EventBridge rule triggers the Lambda function on a schedule.
2. The Lambda function retrieves the FSx for Lustre file system details and Data Repository Association (DRA) information.
3. Based on the configured task type (import or export), the function creates a data repository task.
4. The task execution is monitored, and any errors trigger a CloudWatch alarm, which sends a notification via SNS.

### Cost

You are responsible for the cost of the AWS services used while running this Guidance. As of March 2025, the cost for running this Guidance with the default settings in the US East (N. Virginia) Region is approximately $5.00 per month for processing (assuming daily executions).

We recommend creating a [Budget](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-managing-costs.html) through [AWS Cost Explorer](https://aws.amazon.com/aws-cost-management/aws-cost-explorer/) to help manage costs. Prices are subject to change. For full details, refer to the pricing webpage for each AWS service used in this Guidance.

#### Sample Cost Table

The following table provides a sample cost breakdown for deploying this Guidance with the default parameters in the US East (N. Virginia) Region for one month.

| AWS service  | Dimensions | Cost [USD] |
| ----------- | ------------ | ------------ |
| AWS Lambda | 30 invocations per month, 128 MB memory, 30 second average duration | $0.00 |
| Amazon CloudWatch | 1 custom metric, 1 alarm, 30 data points per month | $1.00 |
| Amazon SNS | 10 email notifications per month | $0.00 |
| AWS CloudFormation | Template and stack management | $0.00 |

## Prerequisites

### Operating System

These deployment instructions are optimized to best work on Amazon Linux 2 AMI. Deployment in another OS may require additional steps.

Required packages:
- AWS CLI (version 2.x or later)
- Python 3.8 or later

To install the AWS CLI on Amazon Linux 2:

```bash
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```

### AWS account requirements

- An existing Amazon FSx for Lustre file system
- An S3 bucket associated with the FSx for Lustre file system via a Data Repository Association (DRA)

## Deployment Steps

1. Clone the repository:

```bash
git clone https://github.com/aws-solutions-library-samples/guidance-for-fsx-for-lustre-data-repository-task-scheduler.git
```

2. Navigate to the cloned directory:

```bash
cd src/cf
```

3. Create a parameters.json file with the following content, replacing the placeholder values:

```json
[
  {
    "ParameterKey": "EmailAddress",
    "ParameterValue": "your-email@example.com"
  },
  {
    "ParameterKey": "Schedule",
    "ParameterValue": "15 6 * * ? *"
  },
  {
    "ParameterKey": "FileSystemId",
    "ParameterValue": "fs-0123456789abcdef0"
  },
  {
    "ParameterKey": "Paths",
    "ParameterValue": "/drt-test"
  },
  {
    "ParameterKey": "TaskType",
    "ParameterValue": "Import"
  }
]
```
### Schedule Configuration

The Schedule parameter uses standard cron expression format with 6 fields:
`minute hour day-of-month month day-of-week year`

Examples:
- `15 6 * * ? *` = Run at 6:15 AM UTC every day
- `0 0/6 * * ? *` = Run every 6 hours
- `0/5 * * * ? *` = Run every 5 minutes
- `0 12 ? * MON-FRI *` = Run at noon UTC Monday through Friday

Common settings:
| Time Pattern | Description |
| ------------ | ----------- |
| `15 6 * * ? *` | Daily at 6:15 AM UTC |
| `0 */12 * * ? *` | Every 12 hours |
| `0 0 1 * ? *` | Monthly on the 1st at midnight UTC |
| `0 8 ? * MON *` | Weekly on Monday at 8:00 AM UTC |

Note: The `?` character is used in the day-of-month or day-of-week field to indicate "no specific value" when the other field has a specific value.

4. Deploy the CloudFormation stack:

```bash
aws cloudformation create-stack \
  --stack-name fsx-drt-scheduler \
  --template-body file://data-repository-task-scheduler.yaml \
  --parameters file://parameters.json \
  --capabilities CAPABILITY_IAM
```

5. Wait for the stack creation to complete:

```aws cloudformation wait stack-create-complete --stack-name fsx-drt-scheduler```

## Deployment Validation

To validate the deployment:

1. Check the CloudFormation stack status:

```bash
aws cloudformation describe-stacks --stack-name fsx-drt-scheduler --query 'Stacks[0].StackStatus'
```

The output should be "CREATE_COMPLETE".

2. Verify the Lambda function was created:

```bash
aws lambda list-functions --query 'Functions[?starts_with(FunctionName, `fsx-drt-scheduler`)].FunctionName'
```

You should see the name of the created Lambda function in the output.

## Running the Guidance

To manually trigger the data repository task:

1. Invoke the Lambda function:

```
aws lambda invoke --function-name <function-name-from-previous-step> --payload '{}' output.json
```

2. Check the output:

```
cat output.json
```

You should see a response containing details about the created data repository task, including its TaskId and Lifecycle status.

## Next Steps

- Modify the Schedule parameter in the CloudFormation template to adjust the frequency of the data repository tasks.
- Customize the Lambda function code to add additional logic or error handling as needed for your specific use case.
- Integrate with other AWS services such as AWS Step Functions for more complex orchestration of data processing workflows.

## Cleanup

To delete all resources created by this Guidance:

1. Delete the CloudFormation stack:

```
aws cloudformation delete-stack --stack-name fsx-drt-scheduler
```

2. Wait for the stack deletion to complete:

```
aws cloudformation wait stack-delete-complete --stack-name fsx-drt-scheduler
```

Note: This will not delete your FSx for Lustre file system or associated S3 bucket. You will need to manage those resources separately.

## License

MIT License

```plaintext
Copyright (c) 2025 Amazon.com

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Version History

### 1.0.0 (2025-03-27)
* Initial release
* Import/Export functionality
* CLI support
* Lambda deployment support
* Comprehensive error handling
* Detailed completion reports

## Support

* Open an issue for bug reports
* Feature requests welcome
* Pull requests encouraged

## Authors

**Romi Asad, romiasad@amazon.com, GitHub: romi1495**

**Tom McDonald, tjm@amazon.com, GitHub: tjmaws**

## Acknowledgments

* AWS FSx for Lustre team
* Open source community
* Original Project contributors

**Darryl Osborne, darrylo@amazon.com,**

**Shrinath Kurdekar, kurdekar@amazon.com, GitHub: Shrinath Kurdekar**

---
