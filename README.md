# CRM AI Agent Benchmarking

A platform for benchmarking AI agents designed for Customer Relationship Management (CRM) tasks.

## System Architecture

The CRM AI Agent Benchmarking system consists of two main components:

1. **Server-Side Application**: A Flask web application hosted on AWS that provides:
   - User registration and authentication
   - Email verification system
   - API key management
   - RESTful API endpoints for score submission and data retrieval
   - Leaderboard for comparing agent performance

2. **Client-Side Library**: A Python library (`crm-benchmark-lib`) that enables developers to:
   - Benchmark their CRM AI agents against standardized datasets
   - Process benchmarks in parallel or asynchronously
   - Submit results to the leaderboard through the API
   - Visualize performance metrics

## Directory Structure

- `/website/`: Server-side Flask application and API
- `/crm_benchmark_lib/`: Python client library for benchmarking
- `/docs/`: Documentation for both server and client components

## Getting Started

### Server Deployment

For deploying the server application on AWS, follow the instructions in:
- [AWS Deployment Guide](website/README_DEPLOYMENT.md)

### Client Library Installation

```bash
pip install crm-benchmark-lib
```

### Basic Usage

```python
from crm_benchmark_lib import BenchmarkClient

# Create a client with your API key
client = BenchmarkClient(
    api_key="your-api-key-here",
    server_url="https://your-domain.com"
)

# Define your agent function
def my_agent(question, data):
    # Your agent implementation here
    return "Agent's answer"

# Run benchmarks and submit results
results = client.run_and_submit(
    agent_callable=my_agent,
    agent_name="My CRM Agent v1.0"
)
```

## Documentation

- [API Documentation](website/API_DOCUMENTATION.md): Details on server API endpoints
- [Client Library Documentation](crm_benchmark_lib/README.md): Usage guide for the Python library

## Development Setup

To set up the development environment:

1. Clone the repository:
```bash
git clone https://github.com/yourusername/CRM-AI-Agent-Benchmarking.git
cd CRM-AI-Agent-Benchmarking
```

2. Install server dependencies:
```bash
cd website
pip install -r requirements.txt
```

3. Install client library in development mode:
```bash
cd ..
pip install -e .
```

4. Create a `.env` file in the website directory:
```
# Flask configuration
FLASK_ENV=development
FLASK_APP=app.py

# Email configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-specific-password
MAIL_DEFAULT_SENDER=your-email@gmail.com

# Security
SECRET_KEY=your-secret-key-here
```

5. Initialize the database:
```bash
cd website
python init_db.py
```

6. Run the server:
```bash
flask run
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 