#!/usr/bin/env python3

from jira import JIRA

import os

JIRA_SERVER = 'https://diversegorgon.atlassian.net'
JIRA_USERNAME = os.environ.get('JIRA_USERNAME')
JIRA_PASSWORD = os.environ.get('JIRA_PASSWORD')
LAST_FETCH_TIME_FILE = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'last_fetch_time')


def get_last_fetch_time():
    """
    Get the last fetch time from the file
    Returns:
        str: The last fetch time (e.g. 2020-06-23 22:13)
    """
    if os.path.exists(LAST_FETCH_TIME_FILE):
        with open(LAST_FETCH_TIME_FILE, 'r') as f:
            last_fetch_time = f.read()

        return last_fetch_time
    return ''


def set_last_fetch_time(last_fetch_time):
    """
    Write the last fetch time to the file
    Args:
        last_fetch_time (str): The fetch time
    """
    with open(LAST_FETCH_TIME_FILE, 'w') as f:
        f.write(last_fetch_time)

class JIRAUtils:
    def __init__(self):
        """
        Connect and authenticate with the jira server
        Returns:
            JIRA object
        """
        self.jira = JIRA(
            options={'server': JIRA_SERVER},
            basic_auth=(JIRA_USERNAME, JIRA_PASSWORD))

    def get_server_name(self):
        base_url = self.jira.server_info()['baseUrl']
        return base_url.split('//')[-1].split('/')[0]

    def get_projects(self):
        """
        Get the list of all projects
        Args:
            jira (JIRA): The JIRA object

        Returns:
            list: The list of projects
        """
        return self.jira.projects()

    def get_issues(self, project, weeks=12):
        """
        Get the list of issues that have been updated since the last time we checked
        Args:
            project (JIRA project): The jira project object to get issues for
            weeks (int): Number of weeks of issues to get
        Returns:
            dict: The issues
                e.g.
                {
                    'summary': [],
                    'assignee': [],
                    'reporter': [],
                    'description': [],
                    'created': [],
                    'updated': [],
                    'labels': [],
                    'status': []
                }
        """
        issues = {
            'summary': [],
            'assignee': [],
            'reporter': [],
            'description': [],
            'created': [],
            'updated': [],
            'labels': [],
            'status': []
        }

        jql = "project={0} AND  updated >= -{1}w".format(project.key, weeks)
        project_issues = self.jira.search_issues(jql, maxResults=False, fields=['summary', 'description', 'comment', 'labels'])

        for issue in project_issues:
            issues['summary'].append(issue.fields.summary or '')
            issues['description'].append(issue.fields.description or '')
            assignee = issue.fields.assignee
            issues['assignee'].append(assignee.displayName if assignee else '')
            reporter = issue.fields.reporter
            issues['reporter'].append(reporter.displayName if reporter else '')
            issues['created'].append(issue.fields.created)
            issues['updated'].append(issue.fields.updated)
            issues['labels'].append(','.join(issue.fields.labels))
            issues['status'].append(issue.fields.status.name)

        return issues

    def get_issues_list(self, project):
        issues = []
        jql = "project={0}".format(project.key)
        project_issues = self.jira.search_issues(jql, maxResults=False,
                                                 fields=['summary', 'description', 'comment', 'labels', 'status', 'created', 'updated', 'priority', 'status', 'issuetype'])

        jira_server_name = self.get_server_name()
        for issue in project_issues:
            issue_key = issue.key
            issue_dict = {
                'jira_server_name': jira_server_name,
                'project_key': project.key,
                'project_name': project.name,
                'key': issue_key,
                'summary': issue.fields.summary,
                'description': issue.fields.description,
                'created': issue.fields.created,
                'updated': issue.fields.updated,
                'priority': issue.fields.priority.name if issue.fields.priority else '',
                'status': issue.fields.status.name if issue.fields.status else '',
                'issue_type': issue.fields.issuetype.name if issue.fields.issuetype else '',
                'assignee': '',
                'labels': [],
                'comments': [],
            }
            for label in issue.fields.labels:
                issue_dict['labels'].append(label)
            for comment in issue.fields.comment.comments:
                issue_dict['comments'].append(comment.body)

            issues.append(issue_dict)

        return issues
