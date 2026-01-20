import * as cdk from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as sns from 'aws-cdk-lib/aws-sns';
import * as stepfunctions from 'aws-cdk-lib/aws-stepfunctions';
import * as sfnTasks from 'aws-cdk-lib/aws-stepfunctions-tasks';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as kms from 'aws-cdk-lib/aws-kms';
import * as events from 'aws-cdk-lib/aws-events';
import * as targets from 'aws-cdk-lib/aws-events-targets';
import { Construct } from 'constructs';

export class DocGeniusWorkerStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Apply tags to all resources in this stack
    cdk.Tags.of(this).add('Team', 'FastAI-DocGeniusWorker');

    // KMS Key for encryption
    const kmsKey = new kms.Key(this, 'DocGeniusWorkerKey', {
      alias: 'docgenius-worker-key',
      description: 'KMS key for DocGenius Worker encryption',
      enableKeyRotation: true,
    });

    // S3 Buckets
    const inputBucket = new s3.Bucket(this, 'InputBucket', {
      bucketName: `docgenius-worker-input-${this.account}`,
      encryption: s3.BucketEncryption.KMS,
      encryptionKey: kmsKey,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      lifecycleRules: [{
        id: 'DeleteAfterOneDay',
        enabled: true,
        expiration: cdk.Duration.days(1),
      }],
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    const outputBucket = new s3.Bucket(this, 'OutputBucket', {
      bucketName: `docgenius-worker-output-${this.account}`,
      encryption: s3.BucketEncryption.KMS,
      encryptionKey: kmsKey,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      lifecycleRules: [{
        id: 'DeleteAfterOneDay',
        enabled: true,
        expiration: cdk.Duration.days(1),
      }],
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    // DynamoDB Table
    const jobTable = new dynamodb.Table(this, 'JobTable', {
      tableName: 'DocGeniusWorkerJobs',
      partitionKey: { name: 'jobId', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      timeToLiveAttribute: 'expiresAt',
      pointInTimeRecovery: true,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    jobTable.addGlobalSecondaryIndex({
      indexName: 'status-index',
      partitionKey: { name: 'status', type: dynamodb.AttributeType.STRING },
    });

    // SNS Topic
    const eventsTopic = new sns.Topic(this, 'EventsTopic', {
      topicName: 'DocGeniusWorkerEvents',
    });

    // Lambda Functions
    const apiHandlerRole = new iam.Role(this, 'ApiHandlerRole', {
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'),
      ],
    });

    inputBucket.grantWrite(apiHandlerRole);
    jobTable.grantWriteData(apiHandlerRole);

    const apiHandler = new lambda.Function(this, 'ApiHandler', {
      runtime: lambda.Runtime.PYTHON_3_9,
      handler: 'api_handler.handler',
      code: lambda.Code.fromAsset('lambda'),
      role: apiHandlerRole,
      timeout: cdk.Duration.seconds(300),
      environment: {
        INPUT_BUCKET: inputBucket.bucketName,
        JOB_TABLE: jobTable.tableName,
        KMS_KEY_ARN: kmsKey.keyArn,
      },
    });

    const specGeneratorRole = new iam.Role(this, 'SpecGeneratorRole', {
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'),
      ],
    });

    inputBucket.grantRead(specGeneratorRole);
    outputBucket.grantWrite(specGeneratorRole);
    jobTable.grantReadWriteData(specGeneratorRole);
    
    specGeneratorRole.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: ['bedrock:InvokeModel'],
      resources: ['*'],
    }));

    const specGenerator = new lambda.Function(this, 'SpecGenerator', {
      runtime: lambda.Runtime.PYTHON_3_9,
      handler: 'spec_generator.handler',
      code: lambda.Code.fromAsset('lambda'),
      role: specGeneratorRole,
      timeout: cdk.Duration.seconds(300),
      memorySize: 1024,
      environment: {
        INPUT_BUCKET: inputBucket.bucketName,
        OUTPUT_BUCKET: outputBucket.bucketName,
        JOB_TABLE: jobTable.tableName,
        BEDROCK_MODEL_ID: 'amazon.nova-micro-v1:0',
        MAX_TOKENS: '4000',
      },
    });

    const cleanupRole = new iam.Role(this, 'CleanupRole', {
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'),
      ],
    });

    inputBucket.grantDelete(cleanupRole);
    outputBucket.grantDelete(cleanupRole);
    jobTable.grantReadWriteData(cleanupRole);

    const cleanup = new lambda.Function(this, 'Cleanup', {
      runtime: lambda.Runtime.PYTHON_3_9,
      handler: 'cleanup.handler',
      code: lambda.Code.fromAsset('lambda'),
      role: cleanupRole,
      timeout: cdk.Duration.seconds(300),
      environment: {
        INPUT_BUCKET: inputBucket.bucketName,
        OUTPUT_BUCKET: outputBucket.bucketName,
        JOB_TABLE: jobTable.tableName,
      },
    });

    const notifyRole = new iam.Role(this, 'NotifyRole', {
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'),
      ],
    });

    eventsTopic.grantPublish(notifyRole);
    outputBucket.grantRead(notifyRole);
    jobTable.grantReadData(notifyRole);

    const notifySuccess = new lambda.Function(this, 'NotifySuccess', {
      runtime: lambda.Runtime.PYTHON_3_9,
      handler: 'notify.success_handler',
      code: lambda.Code.fromAsset('lambda'),
      role: notifyRole,
      environment: {
        SNS_TOPIC_ARN: eventsTopic.topicArn,
        OUTPUT_BUCKET: outputBucket.bucketName,
        JOB_TABLE: jobTable.tableName,
      },
    });

    const notifyFailure = new lambda.Function(this, 'NotifyFailure', {
      runtime: lambda.Runtime.PYTHON_3_9,
      handler: 'notify.failure_handler',
      code: lambda.Code.fromAsset('lambda'),
      role: notifyRole,
      environment: {
        SNS_TOPIC_ARN: eventsTopic.topicArn,
        JOB_TABLE: jobTable.tableName,
      },
    });

    // Step Functions State Machine
    const generateSpecTask = new sfnTasks.LambdaInvoke(this, 'GenerateSpecTask', {
      lambdaFunction: specGenerator,
      outputPath: '$.Payload',
    });

    const notifySuccessTask = new sfnTasks.LambdaInvoke(this, 'NotifySuccessTask', {
      lambdaFunction: notifySuccess,
    });

    const notifyFailureTask = new sfnTasks.LambdaInvoke(this, 'NotifyFailureTask', {
      lambdaFunction: notifyFailure,
    });

    const cleanupTask = new sfnTasks.LambdaInvoke(this, 'CleanupTask', {
      lambdaFunction: cleanup,
    });

    const waitForRetention = new stepfunctions.Wait(this, 'WaitForRetention', {
      time: stepfunctions.WaitTime.duration(cdk.Duration.hours(24)),
    });

    const definition = generateSpecTask
      .addCatch(notifyFailureTask.next(cleanupTask), {
        errors: ['States.ALL'],
      })
      .next(notifySuccessTask)
      .next(waitForRetention)
      .next(cleanupTask);

    const stateMachine = new stepfunctions.StateMachine(this, 'StateMachine', {
      definition,
      timeout: cdk.Duration.minutes(30),
    });

    // Grant Step Functions permission to invoke Lambdas
    specGenerator.grantInvoke(stateMachine.role);
    notifySuccess.grantInvoke(stateMachine.role);
    notifyFailure.grantInvoke(stateMachine.role);
    cleanup.grantInvoke(stateMachine.role);

    // API Gateway
    const api = new apigateway.RestApi(this, 'Api', {
      restApiName: 'DocGenius Worker API',
      description: 'API for AI-driven document generation',
      defaultCorsPreflightOptions: {
        allowOrigins: apigateway.Cors.ALL_ORIGINS,
        allowMethods: apigateway.Cors.ALL_METHODS,
      },
      binaryMediaTypes: [
        'multipart/form-data',
        'multipart/form-data/*',
        'application/octet-stream'
      ],
    });

    const generateSpecIntegration = new apigateway.LambdaIntegration(apiHandler);
    
    api.root.addResource('generate-spec').addMethod('POST', generateSpecIntegration);

    const jobStatusHandler = new lambda.Function(this, 'JobStatusHandler', {
      runtime: lambda.Runtime.PYTHON_3_9,
      handler: 'job_status.handler',
      code: lambda.Code.fromAsset('lambda'),
      environment: {
        JOB_TABLE: jobTable.tableName,
        OUTPUT_BUCKET: outputBucket.bucketName,
      },
    });

    jobTable.grantReadData(jobStatusHandler);
    outputBucket.grantRead(jobStatusHandler);

    const jobStatusIntegration = new apigateway.LambdaIntegration(jobStatusHandler);
    const jobResource = api.root.addResource('job-status');
    jobResource.addResource('{jobId}').addMethod('GET', jobStatusIntegration);

    // EventBridge rule for cleanup
    new events.Rule(this, 'CleanupRule', {
      schedule: events.Schedule.cron({ minute: '0' }),
      targets: [new targets.LambdaFunction(cleanup)],
    });

    // Grant API handler permission to start Step Functions
    stateMachine.grantStartExecution(apiHandlerRole);
    apiHandler.addEnvironment('STATE_MACHINE_ARN', stateMachine.stateMachineArn);

    // Outputs
    new cdk.CfnOutput(this, 'ApiUrl', {
      value: api.url,
      description: 'API Gateway URL',
    });

    new cdk.CfnOutput(this, 'InputBucketName', {
      value: inputBucket.bucketName,
      description: 'Input S3 Bucket Name',
    });

    new cdk.CfnOutput(this, 'OutputBucketName', {
      value: outputBucket.bucketName,
      description: 'Output S3 Bucket Name',
    });
  }
}