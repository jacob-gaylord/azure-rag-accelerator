metadata description = 'Creates a comprehensive RAG-specific dashboard for monitoring Azure RAG Accelerator performance and user experience.'

param applicationInsightsName string
param dashboardName string = '${applicationInsightsName}-rag-dashboard'

resource applicationInsights 'Microsoft.Insights/components@2020-02-02' existing = {
  name: applicationInsightsName
}

resource ragDashboard 'Microsoft.Portal/dashboards@2020-09-01-preview' = {
  name: dashboardName
  location: resourceGroup().location
  properties: {
    lenses: [
      {
        order: 0
        parts: [
          // RAG Performance Overview
          {
            position: { x: 0, y: 0, rowSpan: 4, colSpan: 6 }
            metadata: {
              inputs: [
                {
                  name: 'ComponentId'
                  value: applicationInsights.id
                }
                {
                  name: 'Query'
                  value: '''
                    customMetrics
                    | where name in ("chat_requests_total", "ask_requests_total")
                    | summarize Total_Requests = sum(value) by bin(timestamp, 1h), name
                    | render timechart
                  '''
                }
                {
                  name: 'TimeRange'
                  value: 'PT24H'
                }
                {
                  name: 'Dimensions'
                  value: {
                    xAxis: { name: 'timestamp', type: 'datetime' }
                    yAxis: [{ name: 'Total_Requests', type: 'long' }]
                    splitBy: [{ name: 'name', type: 'string' }]
                    aggregation: 'Sum'
                  }
                }
              ]
              type: 'Extension/Microsoft_OperationsManagementSuite_Workspace/PartType/LogsDashboardPart'
              settings: {
                content: {
                  PartTitle: 'RAG Requests Over Time'
                  PartSubTitle: 'Chat and Ask requests per hour'
                }
              }
            }
          }
          // Response Time Performance
          {
            position: { x: 6, y: 0, rowSpan: 4, colSpan: 6 }
            metadata: {
              inputs: [
                {
                  name: 'ComponentId'
                  value: applicationInsights.id
                }
                {
                  name: 'Query'
                  value: '''
                    customMetrics
                    | where name == "response_time_seconds"
                    | summarize 
                        P50 = percentile(value, 50),
                        P95 = percentile(value, 95),
                        P99 = percentile(value, 99),
                        Avg = avg(value)
                    by bin(timestamp, 15m), tostring(customDimensions.approach)
                    | render timechart
                  '''
                }
                {
                  name: 'TimeRange'
                  value: 'PT24H'
                }
              ]
              type: 'Extension/Microsoft_OperationsManagementSuite_Workspace/PartType/LogsDashboardPart'
              settings: {
                content: {
                  PartTitle: 'Response Time Percentiles'
                  PartSubTitle: 'P50, P95, P99 response times by approach'
                }
              }
            }
          }
          // User Feedback Analysis
          {
            position: { x: 0, y: 4, rowSpan: 4, colSpan: 6 }
            metadata: {
              inputs: [
                {
                  name: 'ComponentId'
                  value: applicationInsights.id
                }
                {
                  name: 'Query'
                  value: '''
                    customMetrics
                    | where name == "feedback_rating"
                    | summarize 
                        Avg_Rating = avg(value),
                        Rating_Count = count(),
                        Positive_Feedback = countif(value >= 4),
                        Negative_Feedback = countif(value <= 2)
                    by bin(timestamp, 1h)
                    | extend Satisfaction_Rate = (Positive_Feedback * 100.0) / Rating_Count
                    | render timechart
                  '''
                }
                {
                  name: 'TimeRange'
                  value: 'PT24H'
                }
              ]
              type: 'Extension/Microsoft_OperationsManagementSuite_Workspace/PartType/LogsDashboardPart'
              settings: {
                content: {
                  PartTitle: 'User Feedback & Satisfaction'
                  PartSubTitle: 'Average rating and satisfaction rate over time'
                }
              }
            }
          }
          // Token Usage and Costs
          {
            position: { x: 6, y: 4, rowSpan: 4, colSpan: 6 }
            metadata: {
              inputs: [
                {
                  name: 'ComponentId'
                  value: applicationInsights.id
                }
                {
                  name: 'Query'
                  value: '''
                    customMetrics
                    | where name == "token_usage_total"
                    | summarize Total_Tokens = sum(value) by bin(timestamp, 1h), tostring(customDimensions.model), tostring(customDimensions.token_type)
                    | render timechart
                  '''
                }
                {
                  name: 'TimeRange'
                  value: 'PT24H'
                }
              ]
              type: 'Extension/Microsoft_OperationsManagementSuite_Workspace/PartType/LogsDashboardPart'
              settings: {
                content: {
                  PartTitle: 'Token Usage by Model'
                  PartSubTitle: 'Prompt and completion tokens per hour'
                }
              }
            }
          }
          // Search Results Quality
          {
            position: { x: 0, y: 8, rowSpan: 4, colSpan: 6 }
            metadata: {
              inputs: [
                {
                  name: 'ComponentId'
                  value: applicationInsights.id
                }
                {
                  name: 'Query'
                  value: '''
                    customMetrics
                    | where name == "search_results_count"
                    | summarize 
                        Avg_Results = avg(value),
                        P50_Results = percentile(value, 50),
                        P95_Results = percentile(value, 95)
                    by bin(timestamp, 15m), tostring(customDimensions.approach)
                    | render timechart
                  '''
                }
                {
                  name: 'TimeRange'
                  value: 'PT24H'
                }
              ]
              type: 'Extension/Microsoft_OperationsManagementSuite_Workspace/PartType/LogsDashboardPart'
              settings: {
                content: {
                  PartTitle: 'Search Results Distribution'
                  PartSubTitle: 'Number of search results returned per query'
                }
              }
            }
          }
          // Citation Engagement
          {
            position: { x: 6, y: 8, rowSpan: 4, colSpan: 6 }
            metadata: {
              inputs: [
                {
                  name: 'ComponentId'
                  value: applicationInsights.id
                }
                {
                  name: 'Query'
                  value: '''
                    customMetrics
                    | where name == "citation_clicks_total"
                    | summarize Total_Clicks = sum(value) by bin(timestamp, 1h), tostring(customDimensions.citation_type)
                    | render timechart
                  '''
                }
                {
                  name: 'TimeRange'
                  value: 'PT24H'
                }
              ]
              type: 'Extension/Microsoft_OperationsManagementSuite_Workspace/PartType/LogsDashboardPart'
              settings: {
                content: {
                  PartTitle: 'Citation Clicks'
                  PartSubTitle: 'User engagement with source citations'
                }
              }
            }
          }
          // Active Sessions
          {
            position: { x: 0, y: 12, rowSpan: 3, colSpan: 4 }
            metadata: {
              inputs: [
                {
                  name: 'ComponentId'
                  value: applicationInsights.id
                }
                {
                  name: 'Query'
                  value: '''
                    customMetrics
                    | where name == "active_sessions"
                    | summarize Active_Sessions = sum(value) by bin(timestamp, 5m)
                    | render timechart
                  '''
                }
                {
                  name: 'TimeRange'
                  value: 'PT4H'
                }
              ]
              type: 'Extension/Microsoft_OperationsManagementSuite_Workspace/PartType/LogsDashboardPart'
              settings: {
                content: {
                  PartTitle: 'Active Sessions'
                  PartSubTitle: 'Number of concurrent user sessions'
                }
              }
            }
          }
          // Error Rate Summary
          {
            position: { x: 4, y: 12, rowSpan: 3, colSpan: 4 }
            metadata: {
              inputs: [
                {
                  name: 'ComponentId'
                  value: applicationInsights.id
                }
                {
                  name: 'Query'
                  value: '''
                    traces
                    | where severityLevel >= 3
                    | summarize Error_Count = count() by bin(timestamp, 15m), operation_Name
                    | render timechart
                  '''
                }
                {
                  name: 'TimeRange'
                  value: 'PT24H'
                }
              ]
              type: 'Extension/Microsoft_OperationsManagementSuite_Workspace/PartType/LogsDashboardPart'
              settings: {
                content: {
                  PartTitle: 'Error Rates by Operation'
                  PartSubTitle: 'Errors and exceptions over time'
                }
              }
            }
          }
          // Top Error Messages
          {
            position: { x: 8, y: 12, rowSpan: 3, colSpan: 4 }
            metadata: {
              inputs: [
                {
                  name: 'ComponentId'
                  value: applicationInsights.id
                }
                {
                  name: 'Query'
                  value: '''
                    traces
                    | where severityLevel >= 3
                    | where timestamp > ago(24h)
                    | summarize Error_Count = count() by tostring(customDimensions.error_type)
                    | top 10 by Error_Count desc
                    | render barchart
                  '''
                }
                {
                  name: 'TimeRange'
                  value: 'PT24H'
                }
              ]
              type: 'Extension/Microsoft_OperationsManagementSuite_Workspace/PartType/LogsDashboardPart'
              settings: {
                content: {
                  PartTitle: 'Top Error Types'
                  PartSubTitle: 'Most common errors in last 24h'
                }
              }
            }
          }
          // User Satisfaction Metrics
          {
            position: { x: 0, y: 15, rowSpan: 4, colSpan: 12 }
            metadata: {
              inputs: [
                {
                  name: 'ComponentId'
                  value: applicationInsights.id
                }
                {
                  name: 'Query'
                  value: '''
                    customMetrics
                    | where name == "feedback_submissions_total"
                    | extend rating_category = tostring(customDimensions.rating_category)
                    | summarize 
                        Total_Feedback = sum(value),
                        Positive = sumif(value, rating_category == "positive"),
                        Neutral = sumif(value, rating_category == "neutral"),
                        Negative = sumif(value, rating_category == "negative")
                    by bin(timestamp, 6h)
                    | extend 
                        Positive_Pct = (Positive * 100.0) / Total_Feedback,
                        Negative_Pct = (Negative * 100.0) / Total_Feedback
                    | project timestamp, Positive_Pct, Negative_Pct, Total_Feedback
                    | render timechart
                  '''
                }
                {
                  name: 'TimeRange'
                  value: 'P7D'
                }
              ]
              type: 'Extension/Microsoft_OperationsManagementSuite_Workspace/PartType/LogsDashboardPart'
              settings: {
                content: {
                  PartTitle: 'User Satisfaction Trends'
                  PartSubTitle: 'Positive vs Negative feedback percentages over 7 days'
                }
              }
            }
          }
        ]
      }
    ]
    metadata: {
      model: {
        timeRange: {
          value: {
            relative: {
              duration: 24
              timeUnit: 1
            }
          }
          type: 'MsPortalFx.Composition.Configuration.ValueTypes.TimeRange'
        }
        filterLocale: {
          value: 'en-us'
        }
        filters: {
          value: {
            MsPortalFx_TimeRange: {
              model: {
                format: 'utc'
                granularity: 'auto'
                relative: '24h'
              }
              displayCache: {
                name: 'UTC Time'
                value: 'Past 24 hours'
              }
              filteredPartIds: [
                'StartboardPart-LogsDashboardPart-0'
                'StartboardPart-LogsDashboardPart-1'
                'StartboardPart-LogsDashboardPart-2'
                'StartboardPart-LogsDashboardPart-3'
                'StartboardPart-LogsDashboardPart-4'
                'StartboardPart-LogsDashboardPart-5'
                'StartboardPart-LogsDashboardPart-6'
                'StartboardPart-LogsDashboardPart-7'
                'StartboardPart-LogsDashboardPart-8'
                'StartboardPart-LogsDashboardPart-9'
              ]
            }
          }
        }
      }
    }
  }
  tags: {
    'hidden-title': 'RAG Performance Dashboard'
    purpose: 'monitoring'
    component: 'observability'
  }
}

output dashboardId string = ragDashboard.id
output dashboardName string = ragDashboard.name 
