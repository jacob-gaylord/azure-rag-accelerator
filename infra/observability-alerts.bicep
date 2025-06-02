metadata description = 'Creates Application Insights alerts for Azure RAG Accelerator observability.'

param applicationInsightsName string
param alertEmailAddress string = ''
param environment string = 'dev'

resource applicationInsights 'Microsoft.Insights/components@2020-02-02' existing = {
  name: applicationInsightsName
}

// Action Group for alert notifications
resource alertActionGroup 'Microsoft.Insights/actionGroups@2023-01-01' = {
  name: '${applicationInsightsName}-alerts'
  location: 'Global'
  properties: {
    groupShortName: 'RAGAlerts'
    enabled: true
    emailReceivers: alertEmailAddress != '' ? [
      {
        name: 'AdminEmail'
        emailAddress: alertEmailAddress
        useCommonAlertSchema: true
      }
    ] : []
  }
}

// High Error Rate Alert
resource highErrorRateAlert 'Microsoft.Insights/metricAlerts@2018-03-01' = {
  name: '${applicationInsightsName}-high-error-rate'
  location: 'Global'
  properties: {
    description: 'Alert when error rate exceeds 5% over 5 minutes'
    severity: 2
    enabled: true
    scopes: [
      applicationInsights.id
    ]
    evaluationFrequency: 'PT1M'
    windowSize: 'PT5M'
    criteria: {
      'odata.type': 'Microsoft.Azure.Monitor.SingleResourceMultipleMetricCriteria'
      allOf: [
        {
          name: 'HighErrorRate'
          metricName: 'requests/failed'
          operator: 'GreaterThan'
          threshold: 5
          timeAggregation: 'Count'
          criterionType: 'StaticThresholdCriterion'
        }
      ]
    }
    actions: [
      {
        actionGroupId: alertActionGroup.id
      }
    ]
  }
}

// High Response Time Alert
resource highResponseTimeAlert 'Microsoft.Insights/metricAlerts@2018-03-01' = {
  name: '${applicationInsightsName}-high-response-time'
  location: 'Global'
  properties: {
    description: 'Alert when average response time exceeds 10 seconds over 5 minutes'
    severity: 2
    enabled: true
    scopes: [
      applicationInsights.id
    ]
    evaluationFrequency: 'PT1M'
    windowSize: 'PT5M'
    criteria: {
      'odata.type': 'Microsoft.Azure.Monitor.SingleResourceMultipleMetricCriteria'
      allOf: [
        {
          name: 'HighResponseTime'
          metricName: 'requests/duration'
          operator: 'GreaterThan'
          threshold: 10000
          timeAggregation: 'Average'
          criterionType: 'StaticThresholdCriterion'
        }
      ]
    }
    actions: [
      {
        actionGroupId: alertActionGroup.id
      }
    ]
  }
}

// Low Feedback Score Alert (Custom Metric)
resource lowFeedbackAlert 'Microsoft.Insights/scheduledQueryRules@2022-06-15' = {
  name: '${applicationInsightsName}-low-feedback-score'
  location: resourceGroup().location
  properties: {
    displayName: 'Low User Feedback Score Alert'
    description: 'Alert when average feedback rating drops below 3.0 over 30 minutes'
    severity: 2
    enabled: true
    evaluationFrequency: 'PT5M'
    windowSize: 'PT30M'
    scopes: [
      applicationInsights.id
    ]
    criteria: {
      allOf: [
        {
          query: '''
            customMetrics
            | where name == "feedback_rating"
            | where timestamp > ago(30m)
            | summarize avg_rating = avg(value) by bin(timestamp, 5m)
            | where avg_rating < 3.0
          '''
          timeAggregation: 'Count'
          operator: 'GreaterThan'
          threshold: 0
          failingPeriods: {
            numberOfEvaluationPeriods: 1
            minFailingPeriodsToAlert: 1
          }
        }
      ]
    }
    actions: {
      actionGroups: [
        alertActionGroup.id
      ]
    }
  }
}

// High Token Usage Alert
resource highTokenUsageAlert 'Microsoft.Insights/scheduledQueryRules@2022-06-15' = {
  name: '${applicationInsightsName}-high-token-usage'
  location: resourceGroup().location
  properties: {
    displayName: 'High Token Usage Alert'
    description: 'Alert when token usage exceeds 100,000 tokens per hour'
    severity: 1
    enabled: true
    evaluationFrequency: 'PT15M'
    windowSize: 'PT1H'
    scopes: [
      applicationInsights.id
    ]
    criteria: {
      allOf: [
        {
          query: '''
            customMetrics
            | where name == "token_usage_total"
            | where timestamp > ago(1h)
            | summarize total_tokens = sum(value)
            | where total_tokens > 100000
          '''
          timeAggregation: 'Count'
          operator: 'GreaterThan'
          threshold: 0
          failingPeriods: {
            numberOfEvaluationPeriods: 1
            minFailingPeriodsToAlert: 1
          }
        }
      ]
    }
    actions: {
      actionGroups: [
        alertActionGroup.id
      ]
    }
  }
}

// Failed Chat Requests Alert
resource failedChatRequestsAlert 'Microsoft.Insights/scheduledQueryRules@2022-06-15' = {
  name: '${applicationInsightsName}-failed-chat-requests'
  location: resourceGroup().location
  properties: {
    displayName: 'Failed Chat Requests Alert'
    description: 'Alert when chat request failures exceed 10 in 15 minutes'
    severity: 2
    enabled: true
    evaluationFrequency: 'PT5M'
    windowSize: 'PT15M'
    scopes: [
      applicationInsights.id
    ]
    criteria: {
      allOf: [
        {
          query: '''
            traces
            | where operation_Name in ("ask_request", "chat_request", "chat_stream_request")
            | where severityLevel >= 3
            | where timestamp > ago(15m)
            | summarize failed_requests = count()
            | where failed_requests > 10
          '''
          timeAggregation: 'Count'
          operator: 'GreaterThan'
          threshold: 0
          failingPeriods: {
            numberOfEvaluationPeriods: 1
            minFailingPeriodsToAlert: 1
          }
        }
      ]
    }
    actions: {
      actionGroups: [
        alertActionGroup.id
      ]
    }
  }
}

// Dependency Failure Alert (Azure OpenAI, Search, etc.)
resource dependencyFailureAlert 'Microsoft.Insights/metricAlerts@2018-03-01' = {
  name: '${applicationInsightsName}-dependency-failures'
  location: 'Global'
  properties: {
    description: 'Alert when dependency failure rate exceeds 5% over 10 minutes'
    severity: 1
    enabled: true
    scopes: [
      applicationInsights.id
    ]
    evaluationFrequency: 'PT1M'
    windowSize: 'PT10M'
    criteria: {
      'odata.type': 'Microsoft.Azure.Monitor.SingleResourceMultipleMetricCriteria'
      allOf: [
        {
          name: 'DependencyFailures'
          metricName: 'dependencies/failed'
          operator: 'GreaterThan'
          threshold: 5
          timeAggregation: 'Count'
          criterionType: 'StaticThresholdCriterion'
        }
      ]
    }
    actions: [
      {
        actionGroupId: alertActionGroup.id
      }
    ]
  }
}

// Availability Alert
resource availabilityAlert 'Microsoft.Insights/metricAlerts@2018-03-01' = {
  name: '${applicationInsightsName}-availability'
  location: 'Global'
  properties: {
    description: 'Alert when application availability drops below 95% over 15 minutes'
    severity: 1
    enabled: true
    scopes: [
      applicationInsights.id
    ]
    evaluationFrequency: 'PT1M'
    windowSize: 'PT15M'
    criteria: {
      'odata.type': 'Microsoft.Azure.Monitor.SingleResourceMultipleMetricCriteria'
      allOf: [
        {
          name: 'LowAvailability'
          metricName: 'availabilityResults/availabilityPercentage'
          operator: 'LessThan'
          threshold: 95
          timeAggregation: 'Average'
          criterionType: 'StaticThresholdCriterion'
        }
      ]
    }
    actions: [
      {
        actionGroupId: alertActionGroup.id
      }
    ]
  }
}

output actionGroupId string = alertActionGroup.id
output alertNames array = [
  highErrorRateAlert.name
  highResponseTimeAlert.name
  lowFeedbackAlert.name
  highTokenUsageAlert.name
  failedChatRequestsAlert.name
  dependencyFailureAlert.name
  availabilityAlert.name
] 
