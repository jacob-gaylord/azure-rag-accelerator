# Admin Dashboard Guide

The Azure RAG Accelerator includes a comprehensive admin dashboard for monitoring feedback, analytics, and chat history. This guide covers setup, usage, and customization of the admin interface.

## 📊 Overview

The admin dashboard provides:
- **Real-time Analytics**: Feedback trends, rating distributions, and session metrics
- **Feedback Management**: View, filter, and export user feedback
- **Chat History**: Monitor conversation patterns and user engagement
- **Data Export**: Export data in CSV or JSON formats
- **Interactive Charts**: Visual representation of key metrics

## 🚀 Getting Started

### Prerequisites

1. **Authentication Enabled**: Admin dashboard requires user authentication
   ```bash
   azd env set AZURE_USE_AUTHENTICATION "true"
   azd up
   ```

2. **User Permissions**: Users must be authenticated via Azure AD to access admin features

3. **Data Available**: Some chat history and feedback data for meaningful analytics

### Accessing the Dashboard

1. **Navigate to your deployed application**
2. **Ensure you're logged in** (via Azure AD authentication)
3. **Go to `/admin`** route: `https://your-app.azurecontainerapps.io/admin`

> **Note**: If you see an access denied error, verify that authentication is enabled and you're properly logged in.

## 🎯 Dashboard Features

### Analytics Tab

The analytics tab provides high-level metrics and trends:

#### Key Metrics Cards
- **Total Feedback**: Number of feedback submissions received
- **Average Rating**: Overall satisfaction rating (1-5 stars)
- **Total Sessions**: Number of chat sessions
- **Total Messages**: Number of messages exchanged

#### Interactive Charts
1. **Feedback Trends**: Line chart showing feedback volume and average ratings over time
2. **Rating Distribution**: Doughnut chart showing the distribution of star ratings
3. **Session Metrics**: Additional charts for session length and engagement patterns

### Feedback Tab

Detailed feedback management interface:

#### Features
- **Real-time Filtering**: Filter by rating, date, user, or session
- **Search Functionality**: Search through feedback comments
- **Sortable Columns**: Click column headers to sort data
- **Detailed View**: See complete feedback with context

#### Filter Options
```bash
# Available filters:
- Rating: Filter by 1-5 star ratings
- Date: Filter by specific date range
- User: Search by user ID
- Session: Search by session ID
- Comment: Text search in feedback comments
```

#### Data Columns
- **Timestamp**: When feedback was submitted
- **Rating**: Star rating (1-5)
- **User**: User identifier
- **Session**: Session identifier
- **Comment**: User's written feedback

### Chat History Tab

Monitor and analyze conversation patterns:

#### Features
- **Session Overview**: View all chat sessions with metadata
- **Message Counts**: Number of messages per session
- **Duration Tracking**: How long users spend in conversations
- **Last Message Preview**: Quick view of recent activity

#### Filter Options
- **Date Range**: Filter sessions by date
- **User**: Search by specific user
- **Session Duration**: Filter by conversation length
- **Message Count**: Filter by conversation depth

#### Data Columns
- **Timestamp**: Session start time
- **User**: User identifier
- **Session ID**: Unique session identifier
- **Messages**: Number of messages in session
- **Duration**: Session length in minutes
- **Last Message**: Preview of final message

## 🔧 Configuration

### Environment Variables

Configure the admin dashboard through environment variables:

```bash
# Enable admin dashboard (required)
AZURE_USE_AUTHENTICATION=true

# Optional: Customize admin access
ADMIN_REQUIRED_ROLE="admin"  # Require specific role
ADMIN_USER_WHITELIST="user1@company.com,user2@company.com"  # Specific users only

# Optional: Export settings
EXPORT_MAX_RECORDS=10000  # Limit export size
EXPORT_TIMEOUT_SECONDS=300  # Export timeout
```

### Cosmos DB Configuration

The dashboard reads data from Cosmos DB containers:

```json
{
  "feedback_container": "UserFeedback",
  "chat_history_container": "ChatHistory",
  "database_name": "CosmosDB"
}
```

### API Endpoints

The dashboard uses these backend endpoints:

- `GET /admin/analytics`: Aggregated metrics and trends
- `GET /admin/feedback`: Feedback data with filtering
- `GET /admin/chat-history`: Chat session data
- `POST /admin/export`: Data export functionality

## 📈 Analytics and Metrics

### Understanding the Data

#### Feedback Metrics
- **Rating Distribution**: Shows user satisfaction patterns
- **Trend Analysis**: Identifies improvement or degradation over time
- **Volume Metrics**: Indicates user engagement levels

#### Session Analytics
- **Average Session Length**: Indicates user engagement depth
- **Messages per Session**: Shows conversation complexity
- **Bounce Rate**: Users who leave after one message

#### Performance Indicators
```bash
# Key KPIs to monitor:
- Average rating > 4.0 (good satisfaction)
- Session length 5-15 minutes (engaged users)
- Bounce rate < 30% (effective first responses)
- Feedback volume growth (increasing adoption)
```

### Setting up Alerts

Configure Application Insights alerts for key metrics:

```bicep
// Example: Alert on low satisfaction
resource lowSatisfactionAlert 'Microsoft.Insights/metricAlerts@2018-03-01' = {
  name: 'low-satisfaction-alert'
  properties: {
    criteria: {
      allOf: [
        {
          metricName: 'average_rating'
          operator: 'LessThan'
          threshold: 3.5
          timeAggregation: 'Average'
        }
      ]
    }
    windowSize: 'PT1H'
    evaluationFreency: 'PT5M'
    severity: 2
  }
}
```

## 📤 Data Export

### Export Formats

1. **CSV Format**: Suitable for Excel analysis
2. **JSON Format**: Suitable for programmatic processing

### Export Process

1. **Select Export Type**: Choose feedback or chat history
2. **Choose Format**: Select CSV or JSON
3. **Apply Filters**: Export only relevant data
4. **Download**: File automatically downloads to browser

### Example Export Data

**Feedback CSV Format**:
```csv
timestamp,rating,userId,sessionId,comment,messageContent
2024-01-15T10:30:00Z,5,user123,session456,"Very helpful!","What are the benefits?"
2024-01-15T11:15:00Z,4,user789,session321,"Good response","How do I request vacation?"
```

**Chat History JSON Format**:
```json
[
  {
    "sessionId": "session456",
    "userId": "user123",
    "timestamp": "2024-01-15T10:30:00Z",
    "messageCount": 5,
    "duration": 450,
    "lastMessage": "Thank you for the information!"
  }
]
```

### Automated Export

Set up automated exports using Azure Logic Apps:

```json
{
  "trigger": {
    "recurrence": {
      "frequency": "Week",
      "interval": 1
    }
  },
  "actions": {
    "export_feedback": {
      "type": "Http",
      "inputs": {
        "method": "POST",
        "uri": "https://your-app.azurecontainerapps.io/admin/export",
        "body": {
          "type": "feedback",
          "format": "csv",
          "dateRange": "last_week"
        }
      }
    }
  }
}
```

## 🎨 Customization

### UI Customization

Modify the dashboard appearance by editing:

```typescript
// app/frontend/src/pages/admin/AdminDashboard.module.css
.adminDashboard {
  /* Customize overall layout */
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
}

.metricCard {
  /* Customize metric cards */
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 12px;
  padding: 24px;
}

.chartCard {
  /* Customize chart containers */
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
```

### Adding Custom Metrics

Add new metrics to the analytics API:

```python
# app/backend/admin_routes.py
@app.route("/admin/analytics")
async def get_admin_analytics():
    # Existing metrics...
    
    # Add custom metric
    custom_metric = await calculate_custom_metric()
    
    return {
        "totalFeedback": total_feedback,
        "averageRating": avg_rating,
        # ... existing metrics
        "customMetric": custom_metric  # New metric
    }
```

Update the frontend to display custom metrics:

```typescript
// app/frontend/src/pages/admin/AdminDashboard.tsx
interface AdminAnalytics {
  totalFeedback: number;
  averageRating: number;
  // ... existing fields
  customMetric: number;  // Add new field
}

// Add custom metric card
<div className={styles.metricCard}>
  <Stack>
    <Text variant="large">{analytics?.customMetric || 0}</Text>
    <Text variant="medium">Custom Metric</Text>
  </Stack>
</div>
```

### Custom Chart Types

Add new chart types using Chart.js:

```typescript
// Install additional chart types
npm install chart.js chartjs-adapter-date-fns

// Add custom chart component
import { Scatter } from 'react-chartjs-2';

const CustomScatterChart = ({ data }) => {
  const chartData = {
    datasets: [{
      label: 'User Engagement',
      data: data.map(item => ({
        x: item.sessionLength,
        y: item.satisfaction
      })),
      backgroundColor: 'rgba(75, 192, 192, 0.6)'
    }]
  };

  return <Scatter data={chartData} options={{
    scales: {
      x: { title: { display: true, text: 'Session Length (minutes)' }},
      y: { title: { display: true, text: 'Satisfaction Rating' }}
    }
  }} />;
};
```

## 🔒 Security Considerations

### Access Control

1. **Authentication Required**: Users must be logged in via Azure AD
2. **Role-Based Access**: Optionally restrict to specific roles
3. **Audit Logging**: All admin actions are logged

### Data Privacy

1. **User Anonymization**: Consider hashing user IDs for privacy
2. **Data Retention**: Implement data retention policies
3. **Export Permissions**: Limit who can export sensitive data

### Security Headers

Ensure proper security headers are set:

```python
# app/backend/app.py
@app.after_request
async def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response
```

## 📊 Performance Optimization

### Database Indexing

Optimize Cosmos DB queries with proper indexing:

```json
{
  "indexingPolicy": {
    "includedPaths": [
      {
        "path": "/timestamp/*"
      },
      {
        "path": "/userId/*"
      },
      {
        "path": "/sessionId/*"
      },
      {
        "path": "/rating/*"
      }
    ]
  }
}
```

### Caching Strategy

Implement caching for better performance:

```python
# app/backend/admin_routes.py
from functools import lru_cache
import asyncio

@lru_cache(maxsize=128)
async def get_cached_analytics(time_bucket):
    """Cache analytics for 5-minute intervals"""
    # Expensive analytics calculation
    return analytics_data

@app.route("/admin/analytics")
async def get_admin_analytics():
    # Use 5-minute time buckets for caching
    current_bucket = int(time.time() // 300) * 300
    return await get_cached_analytics(current_bucket)
```

### Frontend Performance

Optimize React performance:

```typescript
// Use React.memo for expensive components
const ExpensiveChart = React.memo(({ data }) => {
  return <ComplexChart data={data} />;
});

// Implement virtual scrolling for large datasets
import { FixedSizeList as List } from 'react-window';

const VirtualizedFeedbackList = ({ items }) => {
  const Row = ({ index, style }) => (
    <div style={style}>
      <FeedbackRow item={items[index]} />
    </div>
  );

  return (
    <List
      height={600}
      itemCount={items.length}
      itemSize={80}
    >
      {Row}
    </List>
  );
};
```

## 🔍 Troubleshooting

### Common Issues

#### Dashboard Shows No Data

1. **Check authentication**: Ensure user is logged in
2. **Verify data exists**: Check Cosmos DB containers
3. **Test API endpoints**: Manually test `/admin/analytics`

```bash
# Test API endpoint
curl -X GET "https://your-app.azurecontainerapps.io/admin/analytics" \
  -H "Authorization: Bearer $(az account get-access-token --query accessToken -o tsv)"
```

#### Export Not Working

1. **Check browser settings**: Ensure downloads are enabled
2. **Verify API response**: Check network tab for errors
3. **Check file size limits**: Large exports may timeout

```bash
# Test export API
curl -X POST "https://your-app.azurecontainerapps.io/admin/export" \
  -H "Content-Type: application/json" \
  -d '{"type": "feedback", "format": "csv"}'
```

#### Slow Loading Times

1. **Check data volume**: Large datasets slow down queries
2. **Optimize filters**: Use date ranges to limit data
3. **Enable caching**: Implement caching for repeated queries

### Debug Logging

Enable debug logging for the admin dashboard:

```bash
# Set debug environment variable
azd env set LOG_LEVEL "DEBUG"
azd deploy

# View admin-specific logs
az containerapp logs show --name <app> --resource-group <rg> --follow | grep "admin"
```

## 📝 Best Practices

### Data Management

1. **Regular Cleanup**: Archive old data to maintain performance
2. **Data Validation**: Validate data integrity regularly
3. **Backup Strategy**: Implement backup for critical analytics data

### User Experience

1. **Loading States**: Show loading indicators for slow operations
2. **Error Handling**: Provide clear error messages
3. **Responsive Design**: Ensure mobile compatibility

### Monitoring

1. **Usage Analytics**: Track dashboard usage patterns
2. **Performance Metrics**: Monitor response times
3. **Error Tracking**: Log and alert on errors

## 🚀 Advanced Features

### Real-time Updates

Implement real-time dashboard updates using SignalR:

```python
# app/backend/websocket.py
from quart import websocket
import asyncio

@app.websocket('/admin/live')
async def admin_live_updates():
    while True:
        # Get latest metrics
        metrics = await get_realtime_metrics()
        await websocket.send_json(metrics)
        await asyncio.sleep(30)  # Update every 30 seconds
```

```typescript
// app/frontend/src/pages/admin/AdminDashboard.tsx
useEffect(() => {
  const ws = new WebSocket('wss://your-app.azurecontainerapps.io/admin/live');
  
  ws.onmessage = (event) => {
    const metrics = JSON.parse(event.data);
    setAnalytics(metrics);
  };

  return () => ws.close();
}, []);
```

### Custom Dashboards

Allow users to create custom dashboard views:

```typescript
// Custom dashboard builder
const DashboardBuilder = () => {
  const [widgets, setWidgets] = useState([]);
  
  const addWidget = (type: 'chart' | 'metric' | 'table') => {
    const newWidget = {
      id: Date.now(),
      type,
      config: getDefaultConfig(type)
    };
    setWidgets([...widgets, newWidget]);
  };

  return (
    <DragDropContext onDragEnd={onDragEnd}>
      <Droppable droppableId="dashboard">
        {(provided) => (
          <div {...provided.droppableProps} ref={provided.innerRef}>
            {widgets.map((widget, index) => (
              <Draggable key={widget.id} draggableId={widget.id} index={index}>
                {(provided) => (
                  <div
                    ref={provided.innerRef}
                    {...provided.draggableProps}
                    {...provided.dragHandleProps}
                  >
                    <Widget widget={widget} />
                  </div>
                )}
              </Draggable>
            ))}
            {provided.placeholder}
          </div>
        )}
      </Droppable>
    </DragDropContext>
  );
};
```

## 📚 Additional Resources

- [Cosmos DB Query Optimization](https://docs.microsoft.com/azure/cosmos-db/sql-query-getting-started)
- [Chart.js Documentation](https://www.chartjs.org/docs/)
- [React Performance Optimization](https://react.dev/learn/render-and-commit)
- [Application Insights Analytics](https://docs.microsoft.com/azure/azure-monitor/app/analytics)

---

The admin dashboard provides powerful insights into your RAG application's usage and performance. Use these features to monitor user satisfaction, optimize performance, and make data-driven improvements to your application. 