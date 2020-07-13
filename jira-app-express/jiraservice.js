import { config, SQS } from "aws-sdk";
config.update({ region: "us-east-1" });
var sqs = new SQS();
 
const queueUrl = "https://sqs.us-east-1.amazonaws.com/525499439414/atlassian-sqs-lambda-stack-JiraIssuesQueue-P4C0OWB4UO8";

const issueFields = "comment,project,priority,labels,status,summary,description,created,updated,timespent,issuetype,assignee,reporter";
const maxResults = 100;

const getProjects = (httpClient) => {
    return new Promise((resolve, reject) => {

        httpClient.get('/rest/api/2/project', function (err, response, body) {
            if (err) {
                console.log(err);
                reject(err);
            } else {
                const projects = JSON.parse(body);
                resolve(projects)
            }
        });

    });
};


const loadProjectIssues = (httpClient, projectId , startAt) => {
    
    return new Promise((resolve, reject) => {
        
        httpClient.get('/rest/api/2/search?jql=project=' + projectId + '&startAt=' + startAt + '&maxResults=' + maxResults + '&fields=' + issueFields, function (err, response, body) {
            if (err) {
                console.log(err);
                reject(err);
            } else {
                const projectIssues = JSON.parse(body);
                const issues = projectIssues["issues"]
                let issue_promises = []
                startAt = startAt + maxResults;
                issues.forEach(issue =>
                    issue_promises.push(putItOnSQS(issue))
                );
                if (startAt < projectIssues.total) {
                    return loadProjectIssues(httpClient, projectId , startAt)
                }
                Promise.all(issue_promises).then((values) => {
                    resolve(values);
                })

            }
        });


    });
};


const putCreatedOrUpdatedIssueOnTheQueue = (httpClient, issueKey) => {
    return new Promise((resolve, reject) => {

        httpClient.get('/rest/api/2/issue/' + issueKey + '?fields=' + issueFields, function (err, response, body) {
            if (err) {
                console.log(err);
                reject(err);
            } else {
                const issue = JSON.parse(body);

                putItOnSQS(issue).then((data) => {
                    resolve(data);
                })

            }
        });

    });
}

function putItOnSQS(issue) {
    const params = {
        MessageBody: JSON.stringify(sanitizeIssue(issue)),
        QueueUrl: queueUrl
    }
    return sqs.sendMessage(params).promise();

}


const getJiraServerInfo = (httpClient) => {
    return new Promise((resolve, reject) => {
        httpClient.get('/rest/api/3/serverInfo', function (err, response, body) {
            if (err) {
                console.log(err);
                reject(err);
            } else {
                const serverInfo = JSON.parse(body);
                resolve(getHostnameFromRegex(serverInfo.baseUrl));
            }
        });
    });
}

const getHostnameFromRegex = (url) => {
    // run against regex
    const matches = url.match(/^https?\:\/\/([^\/?#]+)(?:[\/?#]|$)/i);
    // extract hostname (will be null if no match is found)
    return matches && matches[1];
}

function sanitizeIssue(issue) {
    let comments = []

    if (issue.fields.comment) {
        let commentsFromIssue = issue.fields.comment.comments;
        commentsFromIssue.forEach((comment) => {
            comments.push(comment.body);
        })
    }

    
    let finalIssue = {}

    finalIssue["issue_id"] = issue.id;
    finalIssue["key"] = issue.key;
    finalIssue["jira_server_name"] = getHostnameFromRegex(issue.self);
    finalIssue["issue_type"] = issue.fields.issuetype.name;
    finalIssue["project_id"] = issue.fields.project.id;
    finalIssue["project_key"] = issue.fields.project.key;
    finalIssue["project_name"] = issue.fields.project.name;
    if (issue.fields.priority)
        finalIssue["priority"] = issue.fields.priority.name;
    else
        finalIssue["priority"] = "";
    finalIssue["labels"] = issue.fields.labels;
    finalIssue["status"] = issue.fields.status.name;
    finalIssue["summary"] = issue.fields.summary;
    finalIssue["description"] = issue.fields.description;
    finalIssue["comments"] = comments;
    finalIssue["created"] = issue.fields.created;
    finalIssue["updated"] = issue.fields.updated;
    finalIssue["time_spent"] = issue.fields.timespent;
    if (issue.fields.assignee){
        finalIssue["assignee"] = issue.fields.assignee.displayName;
        finalIssue["assignee_account_id"] = issue.fields.assignee.accountId;
        finalIssue["assignee_avatar_url"] = issue.fields.assignee.avatarUrls["16x16"];

    }
    else {
        finalIssue["assignee"] = issue.fields.reporter.displayName;
        finalIssue["assignee_account_id"] = issue.fields.reporter.accountId
        finalIssue["assignee_avatar_url"] = issue.fields.reporter.avatarUrls["16x16"]
    }
    
   

    return finalIssue;
}



const _getProjects = getProjects;
export { _getProjects as getProjects };
const _loadProjectIssues = loadProjectIssues;
export { _loadProjectIssues as loadProjectIssues };

const _putCreatedOrUpdatedIssueOnTheQueue = putCreatedOrUpdatedIssueOnTheQueue;
export { _putCreatedOrUpdatedIssueOnTheQueue as putCreatedOrUpdatedIssueOnTheQueue };


const _getJiraServerInfo = getJiraServerInfo;
export { _getJiraServerInfo as getJiraServerInfo };

