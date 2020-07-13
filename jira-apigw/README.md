We're creating an API which will analyze the keywords in the database and provide user suggestions for the given issue.
We're using Chalice to set up an AWS API Gateway backed by a Lambda function.

## Setup
1. Install and set up the aws cli
2. Create a virtual environment and install the dependencies
    ```
    python3 -m venv venv
    . venv/bin/activate
    pip install -r requirements.txt
    ```
3. Run `setup.sh` to copy some utils from the parent directory

## Testing changes locally
Run the Chalice server locally
```
chalice local --port 8001
```

## Deploying the code 
Deploy the API Gateway and Lambda function
```
chalice deploy
```
