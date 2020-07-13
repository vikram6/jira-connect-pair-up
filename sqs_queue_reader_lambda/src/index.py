#!/usr/bin/env python3

import hashlib
import json
from decimal import Decimal
from datetime import datetime

from utils import watson_utils
from utils.ddb_service import DDB

WATSON_RELEVANCE_MINIMUM = 0.4


def lambda_handler(event, context):
    issues = []
    for record in event['Records']:
        issue = json.loads(record["body"])
        issues.append(issue)

    process_issues(issues)


def create_hash(text):
    return hashlib.md5(text.encode('utf-8')).hexdigest()


def get_word_count(text, keywords):
    """
    Args:
        text (str):
        keywords (list):

    Returns:

    """
    count_dict = {}
    for keyword in keywords:
        count_dict[keyword] = text.count(keyword)

    return count_dict


def process_issues(issues):
    """
    Args:
        issues (dict):

    Returns:

    """
    ddb = DDB()
    ddb.create_table(ddb.watson_responses_table_name, 'text_hash')
    ddb.create_table(ddb.issues_with_keywords_table_name, 'server_project_key', 'issue_key')

    watson_responses = []
    issues_with_keywords = []
    text_hashes = {}
    for issue in issues:
        print(issue)
        server_project_key = "{}_{}".format(issue['jira_server_name'], issue['project_key'])
        issue_key = issue['key']
        text_to_analyse = "{0}\n{1}".format(
            issue.get('description', ''),
            issue.get('summary', ''))

        text_hash = create_hash(text_to_analyse)
        # Check if we already have the watson response for this hash
        watson_response = text_hashes.get(text_hash)
        if not watson_response:
            # Check in the database
            watson_response = ddb.get_item_from_db(ddb.watson_responses_table_name, {'text_hash': text_hash})
        if not watson_response:
            # Call the watson api
            watson_response = watson_utils.fn_analyze_text_nlu(text_to_analyse)
            # Convert float to Decimal for the sake of dynamodb
            ddb_watson_response = json.loads(json.dumps(watson_response), parse_float=Decimal)
            ddb_watson_response['text_hash'] = text_hash
            watson_responses.append(ddb_watson_response)
        text_hashes[text_hash] = watson_response

        # Extract the keywords count and insert into the db
        keywords = watson_utils.get_keywords(watson_response, WATSON_RELEVANCE_MINIMUM)
        keywords_count = get_word_count(text_to_analyse, keywords)
        issues_with_keywords.append({
            'server_project_key': server_project_key,
            'issue_key': issue_key,
            'jira_server_name': issue['jira_server_name'],
            'project_key': issue['project_key'],
            'project_name': issue['project_name'],
            'updated': issue['updated'],
            'priority': issue['priority'],
            'status': issue['status'],
            'type': issue['issue_type'],
            'assignee': issue['assignee'],
            'assignee_account_id': issue['assignee_account_id'],
            'assignee_avatar_url': issue['assignee_avatar_url'],
            'keywords': keywords_count
        })

    if watson_responses:
        print("Inserting into Watson DB")
        ddb.batch_write_items(ddb.watson_responses_table_name, watson_responses)
    if issues_with_keywords:
        print("Inserting into Issues DB")
        ddb.batch_write_items(ddb.issues_with_keywords_table_name, issues_with_keywords)


if __name__ == "__main__":
    from utils.jira_utils import JIRAUtils
    jira = JIRAUtils()
    for project in jira.get_projects():
        print("Project: {}".format(project.key))
        issues = jira.get_issues_list(project)
        process_issues(issues)
        break
