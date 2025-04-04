# CRM AI Agent Benchmarking API Documentation

This document provides details on the API endpoints available in the CRM AI Agent Benchmarking system.

## API Base URL

The API is accessible at: `https://your-domain.com/` or the IP address of your deployed server.

## Authentication

All API endpoints require authentication using an API key. This key should be included in the request payload as the `api_key` parameter.

To obtain an API key:
1. Register for an account at `https://your-domain.com/register`
2. Verify your email address
3. Log in to your account
4. View your API key on the profile page

## Endpoints

### Submit Agent Score

**Endpoint**: `/submit_agent_score_api`

**Method**: POST

**Description**: Submit a benchmark score for your agent.

**Request Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| api_key | string | Yes | Your API key |
| agent_name | string | Yes | Name of your agent |
| score | float | Yes | Overall benchmark score (0-100) |
| dataset_scores | object | No | Detailed scores for each dataset |

**Example Request**:
```json
{
  "api_key": "crm-a9c0d68ef00df832fad3159a6befa7ccc92c1551fe1b2699",
  "agent_name": "My CRM Agent v1.0",
  "score": 85.7,
  "dataset_scores": {
    "dataset_1": 90.5,
    "dataset_2": 82.3,
    "dataset_3": 88.1,
    "dataset_4": 81.9,
    "dataset_5": 85.7
  }
}
```

**Example Successful Response**:
```json
{
  "status": "success",
  "message": "Score saved",
  "username": "johndoe"
}
```

**Example Error Response**:
```json
{
  "status": "error",
  "message": "Invalid API key"
}
```

### Get Leaderboard

**Endpoint**: `/api/leaderboard`

**Method**: GET

**Description**: Retrieve the current leaderboard data.

**Query Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| page | integer | No | Page number (default: 1) |
| per_page | integer | No | Results per page (default: 10, max: 50) |

**Example Request**:
```
GET /api/leaderboard?page=1&per_page=10
```

**Example Response**:
```json
{
  "status": "success",
  "leaderboard": [
    {
      "username": "alice",
      "agent_name": "Alice's CRM Agent",
      "score": 92.5,
      "created_at": "2023-07-15T14:30:45"
    },
    {
      "username": "bob",
      "agent_name": "Bob's CRM Helper",
      "score": 89.2,
      "created_at": "2023-07-14T09:15:30"
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 3,
    "total_entries": 27,
    "per_page": 10
  }
}
```

### Get Agent Details

**Endpoint**: `/api/agent/{agent_name}`

**Method**: GET

**Description**: Retrieve detailed information about a specific agent.

**Example Request**:
```
GET /api/agent/Alice%27s%20CRM%20Agent
```

**Example Response**:
```json
{
  "status": "success",
  "agent": {
    "agent_name": "Alice's CRM Agent",
    "username": "alice",
    "latest_score": 92.5,
    "rank": 1,
    "submission_count": 5,
    "first_submission": "2023-06-10T08:45:12",
    "latest_submission": "2023-07-15T14:30:45",
    "dataset_scores": {
      "dataset_1": 94.2,
      "dataset_2": 91.8,
      "dataset_3": 93.5,
      "dataset_4": 90.1,
      "dataset_5": 92.9
    },
    "history": [
      {
        "date": "2023-07-15T14:30:45",
        "score": 92.5
      },
      {
        "date": "2023-07-01T16:20:30",
        "score": 90.8
      }
    ]
  }
}
```

### Error Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Request successful |
| 400 | Bad request - Invalid parameters |
| 403 | Forbidden - Invalid or missing API key |
| 404 | Not found - Requested resource not found |
| 500 | Server error |

## Usage with the CRM Benchmark Library

The easiest way to use the API is with our Python library:

```python
from crm_benchmark_lib import BenchmarkClient

# Create a client with your API key
client = BenchmarkClient(
    api_key="your-api-key-here",
    server_url="https://your-domain.com"
)

# Define your agent function
def my_agent(question, data):
    # Your agent code here
    return answer

# Run benchmarks and submit results
results = client.run_and_submit(
    agent_callable=my_agent,
    agent_name="My CRM Agent v1.0"
)
```

## Rate Limiting

To ensure fair usage, the API implements rate limiting:
- Maximum 60 requests per minute per IP address
- Maximum 10 score submissions per hour per user

## Support

If you encounter any issues or have questions about the API, please contact us at support@your-domain.com. 