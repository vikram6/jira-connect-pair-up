import { config, DynamoDB } from "aws-sdk";
config.update({region: "us-east-1"});

var documentClient = new DynamoDB.DocumentClient();




  async function getProjectsFromDDb(){

    var params = {
        TableName: 'JiraAnalysisTable'
    };
      
      
    return await documentClient.scan(params).promise();
 } 

 const deleteProjectData = (projectKey) => {

  
}

const _deleteProjectData = deleteProjectData;
export { _deleteProjectData as deleteProjectData };



