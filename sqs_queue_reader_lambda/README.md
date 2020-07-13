We're creating an AWS SQS and Lambda function to process new/updated JIRA issues. We use the Watson API to calculate 
the keywords and store the results in an AWS DynamoDB database.

## Setup
1. Install and set up the aws cli
2. Create a virtual environment and install the dependencies
    ```
    python3 -m venv venv
    . venv/bin/activate
    pip install -r requirements-dev.txt --target cloudformation/python_deps
    ```

## Deploying the code
Deploy the Cloudformation template
```
cd cloudformation
./layers_cfn_run.sh
./cfn_run.sh
```