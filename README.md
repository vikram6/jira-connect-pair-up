# jira-connect-pair-up
Pair Up is an Atlassian Connect app that helps you solve your JIRA issues more efficiently by connecting you with people in your company who have worked on similar issues in the past.

## How it works
The app imports JIRA issues as they're created/updated and uses Watson to analyze the issues and suggest users who can help with those issues. The app consists of 3 parts - 
* [The JIRA connect app](https://github.com/vikram6/jira-connect-pair-up/tree/master/jira-app-express) - This is the front end of the app that creates the issue glance
* [The issues processor](https://github.com/vikram6/jira-connect-pair-up/tree/master/sqs_queue_reader_lambda) - Process new/updated issues into our database
* [API](https://github.com/vikram6/jira-connect-pair-up/tree/master/jira-apigw) - Analyze the keywords in issues and provide user suggestions

