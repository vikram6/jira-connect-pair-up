//import getProjectsFromDDb from '../dbservice';
import { getProjects } from '../jiraservice'
import { loadProjectIssues } from '../jiraservice';
import { putCreatedOrUpdatedIssueOnTheQueue } from '../jiraservice';
import { getJiraServerInfo } from '../jiraservice';
import { runInNewContext } from 'vm';
import got from 'got';
import process from 'process';

// [
//     { group: "A", value: 7 },
//     { group: "B", value: 1 },
//     { group: "C", value: 20 },
//     { group: "D", value: 10 }
//   ]
function transformForOutput(response) {

    let projects = Object.keys(response);
    let finalProjects = {};

    for (let i = 0; i < projects.length; i++) {
        let words = Object.keys(response[projects[i]]["keywords"]);
        let d3_resp = [];
        for (let j = 0; j < words.length; j++) {
            d3_resp.push({ "group": words[j], "value": response[projects[i]]["keywords"][words[j]] })
        }

        finalProjects[projects[i]] = d3_resp;
    }

    return finalProjects
}


export default function routes(app, addon, cors) {
    // Redirect root path to /atlassian-connect.json,
    // which will be served by atlassian-connect-express.
    app.get('/', (req, res) => {
        res.redirect('/atlassian-connect.json');
    });

    // This is an example route used by "generalPages" module (see atlassian-connect.json).
    // Verify that the incoming request is authenticated with Atlassian Connect.
    app.get('/hello-world', addon.authenticate(), (req, res, next) => {
        // Rendering a template is easy; the render method takes two params:
        // name of template and a json object to pass the context in.
        var httpClient = addon.httpClient(req);
        getProjects(httpClient).then((projects) => {
            res.render('hello-world', {
                title: 'Projects',
                projects: projects
            });
        })



    });


    app.get('/project-details', addon.checkValidToken(), (req, res, next) => {
        // Rendering a template is easy; the render method takes two params:
        // name of template and a json objgect to pass the context in.
        const projectKey = req.query.key;
        res.render('project-details-charts', {
            ProjectName: projectKey
        });


    });

    app.get('/suggestion-panel', addon.authenticate(), (req, res, next) => {
        // Rendering a template is easy; the render method takes two params:
        // name of template and a json objgect to pass the context in.
        console.log("-----------");
        console.log(req.query);
        console.log("-----------");

        res.render('suggestion-panel', {
            ProjectName: "projectKey"
        });
    });

    app.get('/suggested-users', addon.authenticate(), (req, res, next) => {

        var httpClient = addon.httpClient(req);
        var projectKey = req.query.projectKey;
        var issueKey = req.query.issueKey;

        (async () => {
            try {
                const serverName = await getJiraServerInfo(httpClient);
                const apiKey = process.env["JIRAAPIGWKEY"];
                const url = 'https://941yp9qwxc.execute-api.us-east-1.amazonaws.com/api/related_users?jira_server_name=' + serverName + '&api_key='+apiKey+'&project_key=' + projectKey + '&issue_key=' + issueKey;
                console.log("----URL-----")
                console.log(url);
                console.log("----URL-----")
                const response = await got(url);

                let resp = JSON.parse(response.body)
                res.json(resp);

            } catch (error) {
                next(error)
            }
        })();


    });


    app.get('/project-word-counts', addon.checkValidToken(), (req, res, next) => {
        // Rendering a template is easy; the render method takes two params:
        // name of template and a json object to pass the context in.
        const projectKey = req.query.key;

        (async () => {
            try {
                const response = await got('https://941yp9qwxc.execute-api.us-east-1.amazonaws.com/api/keywords?jira_server_name=diversegorgon.atlassian.net&api_key=foo&projects=' + projectKey);

                let resp = JSON.parse(response.body)
                // const transformedOutput = transformForOutput(resp)
                res.json(resp);
                //=> '<!doctype html> ...'
            } catch (error) {
                next(error)
                //=> 'Internal server error ...'
            }
        })();

    });


    app.get('/execute-full-load', addon.checkValidToken(), (req, res) => {
        var httpClient = addon.httpClient(req);
        // res.json({
        //     "execution-success": "true"
        // });
        getProjects(httpClient).then((projects) => {
            let project_promises = [];
            const startAt = 0;
            projects.forEach(project =>
                project_promises.push(loadProjectIssues(httpClient, project.id, startAt))
            );
            Promise.all(project_promises).then(values => {
                res.json({
                    "execution-success": "true"
                });
            });
        })


    });

    app.get('/execute-full-load-for-project', addon.checkValidToken(), (req, res) => {
        var httpClient = addon.httpClient(req);

        
        let project_promises = [];
        const startAt = 0;
        const projectId = req.query.projectId
        project_promises.push(loadProjectIssues(httpClient, projectId, startAt))

        Promise.all(project_promises).then(values => {
            res.json({
                "execution-success": "true"
            });
        });

        

    });

    // WEB HOOKS
    app.post('/issue-created-updated', addon.authenticate(), (req, res, next) => {
        console.log("------WEB HOOK RECEIVED FOR -----------");
        console.log(req.query.issue);
        console.log("------WEB HOOK RECEIVED FOR -----------");

        var httpClient = addon.httpClient(req);
        putCreatedOrUpdatedIssueOnTheQueue(httpClient, req.query.issue).then((data) => {
            res.json({
                "SUCCESS": true
            });
        }).catch((err) => {
            next(err);
        });


    });

    app.post('/project-deleted', addon.authenticate(), (req, res, next) => {
        console.log("------WEB HOOK RECEIVED FOR Project deleted -----------");
        console.log(req.query.project);

        var httpClient = addon.httpClient(req);
        putCreatedOrUpdatedIssueOnTheQueue(httpClient, req.query.issue).then((data) => {
            res.json({
                "SUCCESS": true
            });
        }).catch((err) => {
            next(err);
        });


    });



    //THIS IS TO TEST LOCALLY
    app.get('/public-page', (req, res) => {
        // Rendering a template is easy; the render method takes two params:
        // name of template and a json object to pass the context in.

        const projects = [{ "expand": "description,lead,issueTypes,url,projectKeys,permissions,insight", "self": "https://diversegorgon.atlassian.net/rest/api/2/project/10000", "id": "10000", "key": "MYF", "name": "MyFirstProduct", "avatarUrls": { "48x48": "https://diversegorgon.atlassian.net/secure/projectavatar?pid=10000&avatarId=10405", "24x24": "https://diversegorgon.atlassian.net/secure/projectavatar?size=small&s=small&pid=10000&avatarId=10405", "16x16": "https://diversegorgon.atlassian.net/secure/projectavatar?size=xsmall&s=xsmall&pid=10000&avatarId=10405", "32x32": "https://diversegorgon.atlassian.net/secure/projectavatar?size=medium&s=medium&pid=10000&avatarId=10405" }, "projectTypeKey": "software", "simplified": true, "style": "next-gen", "isPrivate": false, "properties": {}, "entityId": "4ba4fb15-e846-4fdb-b8c5-6758b67b1178", "uuid": "4ba4fb15-e846-4fdb-b8c5-6758b67b1178" }, { "expand": "description,lead,issueTypes,url,projectKeys,permissions,insight", "self": "https://diversegorgon.atlassian.net/rest/api/2/project/10001", "id": "10001", "key": "AH", "name": "Atlassian Hackathon", "avatarUrls": { "48x48": "https://diversegorgon.atlassian.net/secure/projectavatar?pid=10001&avatarId=10418", "24x24": "https://diversegorgon.atlassian.net/secure/projectavatar?size=small&s=small&pid=10001&avatarId=10418", "16x16": "https://diversegorgon.atlassian.net/secure/projectavatar?size=xsmall&s=xsmall&pid=10001&avatarId=10418", "32x32": "https://diversegorgon.atlassian.net/secure/projectavatar?size=medium&s=medium&pid=10001&avatarId=10418" }, "projectTypeKey": "software", "simplified": false, "style": "classic", "isPrivate": false, "properties": {} }, { "expand": "description,lead,issueTypes,url,projectKeys,permissions,insight", "self": "https://diversegorgon.atlassian.net/rest/api/2/project/10002", "id": "10002", "key": "TJS", "name": "MyThreeJSClone", "avatarUrls": { "48x48": "https://diversegorgon.atlassian.net/secure/projectavatar?pid=10002&avatarId=10404", "24x24": "https://diversegorgon.atlassian.net/secure/projectavatar?size=small&s=small&pid=10002&avatarId=10404", "16x16": "https://diversegorgon.atlassian.net/secure/projectavatar?size=xsmall&s=xsmall&pid=10002&avatarId=10404", "32x32": "https://diversegorgon.atlassian.net/secure/projectavatar?size=medium&s=medium&pid=10002&avatarId=10404" }, "projectTypeKey": "business", "simplified": false, "style": "classic", "isPrivate": false, "properties": {} }, { "expand": "description,lead,issueTypes,url,projectKeys,permissions,insight", "self": "https://diversegorgon.atlassian.net/rest/api/2/project/10005", "id": "10005", "key": "MF", "name": "MyFireCrackerClone", "avatarUrls": { "48x48": "https://diversegorgon.atlassian.net/secure/projectavatar?pid=10005&avatarId=10411", "24x24": "https://diversegorgon.atlassian.net/secure/projectavatar?size=small&s=small&pid=10005&avatarId=10411", "16x16": "https://diversegorgon.atlassian.net/secure/projectavatar?size=xsmall&s=xsmall&pid=10005&avatarId=10411", "32x32": "https://diversegorgon.atlassian.net/secure/projectavatar?size=medium&s=medium&pid=10005&avatarId=10411" }, "projectTypeKey": "software", "simplified": false, "style": "classic", "isPrivate": false, "properties": {} }]

        const projectsFromDDb = getProjectsFromDDb()
        projectsFromDDb.then(function (items) {
            res.render('public', {
                title: 'Test Project Analysis',
                projects: projects

                //issueId: req.query['issueId']
            });
        });

    });

    //SAMPLE TO TEST OUT AJAX REQUEST
    app.get('/test', cors(), (req, res, next) => {
        // Rendering a template is easy; the render method takes two params:
        // name of template and a json object to pass the context in.
        // (async () => {
        //     try {
        //         const response = await got('https://941yp9qwxc.execute-api.us-east-1.amazonaws.com/api/keywords?jira_server_name=diversegorgon.atlassian.net&api_key=foo');

        //         let resp = JSON.parse(response.body)
        //         res.render('hello-world-test', {
        //             title: 'Project Analysis',
        //             projects: Object.keys(resp),
        //             projectData: encodeURIComponent(JSON.stringify(transformForOutput(resp)))
        //             //issueId: req.query['issueId ']
        //         });
        //         //=> '<!doctype html> ...'
        //     } catch (error) {
        //         next(error)
        //         //=> 'Internal server error ...'
        //     }
        // })();
        const projectKey = "BAD";
        (async () => {
            try {
                const response = await got('https://941yp9qwxc.execute-api.us-east-1.amazonaws.com/api/keywords?jira_server_name=diversegorgon.atlassian.net&api_key=foo&projects=' + projectKey);

                let resp = JSON.parse(response.body)
                const transformedOutput = transformForOutput(resp)
                console.log(transformedOutput);
                res.json(transformedOutput);
                //=> '<!doctype html> ...'
            } catch (error) {
                next(error)
                //=> 'Internal server error ...'
            }
        })();

    });
    // Add additional route handlers here...
}
