#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { DocGeniusWorkerStack } from '../lib/docgenius-worker-stack';

const app = new cdk.App();
new DocGeniusWorkerStack(app, 'DocGeniusWorker', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: 'us-east-1', // Cheapest region for Bedrock
  },
});