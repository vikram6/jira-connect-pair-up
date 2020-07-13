from chalice import Chalice, BadRequestError, UnauthorizedError
from chalicelib.utils.ddb_service import DDB
from chalicelib.utils import network_utils
from boto3.dynamodb.conditions import Key
import boto3


ssm = boto3.client('ssm')
parameter = ssm.get_parameter(Name='jiraapigwkey', WithDecryption=True)
VALID_API_KEY = parameter['Parameter']['Value']


app = Chalice(app_name='jira-apigw')

KEYWORDS_EXCLUDE = {
    'None': None
}


@app.route('/related_users', cors=True)
def related_users():
    params = app.current_request.query_params or {}
    print(params)
    jira_server_name = params.get('jira_server_name')
    api_key = params.get('api_key')
    validate_params(jira_server_name, api_key)

    project_key = params.get('project_key')
    issue_key = params.get('issue_key')

    users, related_keywords = get_related_users(jira_server_name, project_key, issue_key)
    return {
        'assignees': users,
        'keywords': related_keywords
    }


def get_related_users(jira_server_name, project_key, current_issue_key):
    ddb = DDB()
    current_issue_assignee = ''
    keywords_in_current_issue = []
    keyword_issues_map = {}
    issue_assignee_map = {}
    assignee_details_map = {}
    network_data = {'Concepts': {'edges': {}, 'nodes': {}}, 'PeopleConcepts': {'edges': {}, 'nodes': {}}}
    server_project_key = "{}_{}".format(jira_server_name, project_key)
    key_condition = Key('server_project_key').eq(server_project_key)
    attributes_to_get = 'keywords,issue_key,assignee,assignee_account_id,assignee_avatar_url'
    for issues in ddb.query(ddb.issues_with_keywords_table_name, key_condition, attributes_to_get):
        for issue in issues:
            if issue['issue_key'] == current_issue_key:
                keywords_in_current_issue = list(issue['keywords'].keys())
                current_issue_assignee = issue['assignee']

            if not issue['assignee']:
                continue
            issue_assignee_map[issue['issue_key']] = issue['assignee']
            if not issue_assignee_map.get(issue['assignee']):
                assignee_details_map[issue['assignee']] = {
                    'assignee_account_url': "https://{0}/jira/people/{1}".format(jira_server_name, issue['assignee_account_id']),
                    'assignee_avatar_url': issue['assignee_avatar_url']
                }
            keywords_count = {}
            for keyword, count in issue['keywords'].items():
                if keyword in KEYWORDS_EXCLUDE:
                    continue
                keywords_count[keyword] = int(count)
                keyword_issues_map.setdefault(keyword, [])
                keyword_issues_map[keyword].append(issue['issue_key'])

            network_data = network_utils.fn_create_overall_indedges(keywords_count, network_data, 'Concepts')
            network_data = network_utils.fn_create_pplconcept_indedges(keywords_count, network_data,
                                                                       issue['assignee'], 'PeopleConcepts')

    # Get related users and keywords
    graphs = network_utils.fn_create_complete_network(network_data)
    text_keywords, users = network_utils.fn_analyze_issuedesc(graphs, keywords_in_current_issue)
    if current_issue_assignee:
        users.remove(current_issue_assignee)

    # Get issues which have the above keywords and the above users
    users_and_related_issues = {}
    for keyword in text_keywords:
        issues = keyword_issues_map[keyword]
        for issue_key in issues:
            assignee = issue_assignee_map[issue_key]
            if assignee in users:
                users_and_related_issues.setdefault(assignee, set())
                users_and_related_issues[assignee].add(issue_key)

    # Prepare the list that needs to be returned
    users_final = []
    sorted_users_and_related_issues = sorted(users_and_related_issues.items(), key=lambda x: len(x[1]), reverse=True)
    for user, issues in sorted_users_and_related_issues:
        issues_list = list(issues)
        users_final.append({
            'assignee': user,
            'assignee_account_url': assignee_details_map[user]['assignee_account_url'],
            'assignee_account_avatar': assignee_details_map[user]['assignee_avatar_url'],
            'issues_url': "https://{0}/browse/{1}?jql=key in ('{2}') order by key".format(jira_server_name, issues_list[0], "','".join(issues_list)),
            'issues': issues_list,
        })

    # Return the top 10 keywords and the top 3 users
    text_keywords = text_keywords[:10]
    users_final = users_final[:3]
    return users_final, text_keywords


def validate_params(jira_server_name, api_key):
    if not jira_server_name:
        raise BadRequestError("'jira_server_name' is required.")
    if not api_key:
        raise BadRequestError("'api_key' was not provided.")
    if not validate_api_key(api_key):
        raise UnauthorizedError("'api_key' is not valid")


def validate_api_key(api_key):
    return api_key == VALID_API_KEY

