from chalice import Chalice, BadRequestError, UnauthorizedError
from chalicelib.utils.ddb_service import DDB
from chalicelib.utils import network_utils
from boto3.dynamodb.conditions import Key

from dateutil.relativedelta import relativedelta
from datetime import datetime
import pprint


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
                users_and_related_issues.setdefault(assignee, [])
                users_and_related_issues[assignee].append(issue_key)

    # Prepare the list that needs to be returned
    users_final = []
    sorted_users_and_related_issues = sorted(users_and_related_issues.items(), key=lambda x: len(x[1]), reverse=True)
    for user, issues in sorted_users_and_related_issues:
        issues = users_and_related_issues[user]
        users_final.append({
            'assignee': user,
            'assignee_account_url': assignee_details_map[user]['assignee_account_url'],
            'assignee_account_avatar': assignee_details_map[user]['assignee_avatar_url'],
            'issues_url': "https://{0}/browse/{1}?jql=key in ('{2}') order by key".format(jira_server_name, issues[0], "','".join(issues)),
            'issues': issues,
        })

    # Return the top 10 keywords and the top 3 users
    text_keywords = text_keywords[:10]
    users_final = users_final[:3]
    return users_final, text_keywords


@app.route('/keywords', cors=True)
def keywords():
    params = app.current_request.query_params or {}
    print(params)
    jira_server_name = params.get('jira_server_name')
    api_key = params.get('api_key')
    validate_params(jira_server_name, api_key)
    date_range = params.get('date_range')
    date_range_arg = get_date_range_arg(date_range)

    projects = params.get('projects')
    projects_list = projects.split(',') if projects else []
    if projects_list:
        keywords_by_proj = get_keywords(jira_server_name, projects_list, date_range_arg)
    else:
        keywords_by_proj = get_keywords_scan(jira_server_name, date_range_arg)

    return keywords_by_proj


# @app.route('/keywords_centrality', cors=True)
# def keywords_centrality():
#     params = app.current_request.query_params or {}
#     print(params)
#     jira_server_name = params.get('jira_server_name')
#     api_key = params.get('api_key')
#     validate_params(jira_server_name, api_key)
#
#     projects = params.get('projects')
#     projects_list = projects.split(',') if projects else []
#     keywords_by_proj = get_keywords_centrality(jira_server_name, projects_list)
#
#     return keywords_by_proj


def get_keywords(jira_server_name, projects, date_range_arg):
    keywords_by_proj = {}
    keywords_by_proj_sorted = {}
    project_keys = {}
    ddb = DDB()
    attributes_to_get = 'keywords,updated,project_name'
    for project_key in projects:
        keywords_by_proj[project_key] = {}
        server_project_key = "{}_{}".format(jira_server_name, project_key)
        key = Key('server_project_key').eq(server_project_key)
        for issues in ddb.query(ddb.issues_with_keywords_table_name, key, attributes_to_get):
            for issue in issues:
                if date_range_arg:
                    updated = datetime.strptime(issue['updated'].split('T')[0], '%Y-%m-%d')
                    oldest_date = datetime.now() + relativedelta(**date_range_arg)
                    if updated < oldest_date:
                        continue

                for keyword in issue['keywords']:
                    if keyword in KEYWORDS_EXCLUDE:
                        continue
                    keywords_by_proj[project_key].setdefault(keyword, 0)
                    keywords_by_proj[project_key][keyword] += int(issue['keywords'][keyword])

                if project_key not in project_keys:
                    project_keys[project_key] = issue['project_name']

        keywords_by_proj_sorted[project_key] = {
            'project_name': project_keys.get(project_key, ''),
            'keywords': {}
        }
        keywords_sorted = sorted(keywords_by_proj[project_key].items(), key=lambda x: x[1], reverse=True)[:10]
        for keyword, count in keywords_sorted:
            keywords_by_proj_sorted[project_key]['keywords'][keyword] = count

    return keywords_by_proj_sorted


def get_keywords_scan(jira_server_name, date_range_arg):
    keywords_by_proj = {}
    keywords_by_proj_sorted = {}
    project_keys = {}
    ddb = DDB()
    attributes_to_get = 'project_key,project_name,jira_server_name,keywords,updated'
    for issues in ddb.scan(ddb.issues_with_keywords_table_name, attributes_to_get):
        for issue in issues:
            if jira_server_name != issue['jira_server_name']:
                continue

            if date_range_arg:
                updated = datetime.strptime(issue['updated'].split('T')[0], '%Y-%m-%d')
                oldest_date = datetime.now() + relativedelta(**date_range_arg)
                if updated < oldest_date:
                    continue

            project_key = issue['project_key']
            project_name = issue['project_name']
            if project_key not in project_keys:
                project_keys[project_key] = project_name
            keywords_by_proj.setdefault(project_key, {})
            for keyword in issue['keywords']:
                if keyword in KEYWORDS_EXCLUDE:
                    continue
                keywords_by_proj[project_key].setdefault(keyword, 0)
                keywords_by_proj[project_key][keyword] += int(issue['keywords'][keyword])

    for project_key in keywords_by_proj:
        keywords_by_proj_sorted[project_key] = {
            'project_name': project_keys[project_key],
            'keywords': {}
        }
        keywords_sorted = sorted(keywords_by_proj[project_key].items(), key=lambda x: x[1], reverse=True)[:10]
        for keyword, count in keywords_sorted:
            keywords_by_proj_sorted[project_key]['keywords'][keyword] = count

    return keywords_by_proj_sorted


def get_keywords_centrality(jira_server_name, projects):
    graph_results_by_proj = {}
    network_data_by_proj = {}

    ddb = DDB()
    attributes_to_get = 'project_name,jira_server_name,keywords'
    for issues in ddb.scan(ddb.issues_with_keywords_table_name, attributes_to_get):
        for issue in issues:
            if jira_server_name != issue['jira_server_name']:
                continue

            project_name = issue['project_name']
            if projects and project_name not in projects:
                continue

            network_data_by_proj.setdefault(project_name, {'edges': {}, 'nodes': {}})
            keywords_dict = {}
            for keyword, count in issue['keywords'].items():
                if keyword in KEYWORDS_EXCLUDE:
                    continue
                keywords_dict[keyword] = int(count)
            network_data_by_proj[project_name] = network_utils.fn_create_overall_indedges(keywords_dict, network_data_by_proj[project_name])

    for project, network_data in network_data_by_proj.items():
        graph_results_by_proj[project] = network_utils.old_fn_create_complete_network(network_data)

    return graph_results_by_proj


def get_date_range_arg(date_range):
    if date_range == '1w':
        date_range_arg = {'weeks': -1}
    elif date_range == '1m':
        date_range_arg = {'months': -1}
    elif date_range == '3m':
        date_range_arg = {'months': -3}
    elif date_range == '6m':
        date_range_arg = {'months': -6}
    elif date_range == '1y':
        date_range_arg = {'years': -1}
    else:
        date_range_arg = {}
    return date_range_arg


def validate_params(jira_server_name, api_key):
    if not jira_server_name:
        raise BadRequestError("'jira_server_name' is required.")
    if not api_key:
        raise BadRequestError("'api_key' was not provided.")
    if not validate_api_key(jira_server_name, api_key):
        raise UnauthorizedError("'api_key' ia valid")


def validate_api_key(jira_server_name, api_key):
    return True
