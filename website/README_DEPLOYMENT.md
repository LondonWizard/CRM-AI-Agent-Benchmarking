# CRM AI Agent Benchmarking - AWS Deployment Guide

This document provides instructions for deploying the CRM AI Agent Benchmarking application on an AWS EC2 Ubuntu server.

## Prerequisites

- An AWS account
- Basic familiarity with AWS EC2
- A domain name (optional but recommended for HTTPS)

## Step 1: Launch an EC2 Instance

1. Sign in to the AWS Management Console
2. Navigate to EC2 Dashboard
3. Click "Launch Instance"
4. Choose an Ubuntu Server 20.04 LTS AMI
5. Select an instance type (t2.micro is sufficient for starting)
6. Configure instance details (default settings are fine for basic deployment)
7. Add storage (at least 8GB)
8. Configure security groups:
   - Allow HTTP (port 80)
   - Allow HTTPS (port 443)
   - Allow SSH (port 22)
9. Review and launch
10. Create or select an existing key pair for SSH access

## Step 2: Set Up the Server

1. Connect to your instance via SSH:
   ```
   ssh -i your-key.pem ubuntu@your-instance-public-dns
   ```

2. Update packages:
   ```
   sudo apt update
   sudo apt upgrade -y
   ```

3. Install required dependencies:
   ```
   sudo apt install -y python3-pip python3-dev build-essential libssl-dev libffi-dev python3-setuptools python3-venv nginx
   ```

## Step 3: Deploy the Application

1. Create a directory for the application:
   ```
   mkdir -p /home/ubuntu/crm-benchmark
   ```

2. Clone the repository or upload your code:
   ```
   git clone https://github.com/yourusername/CRM-AI-Agent-Benchmarking.git /home/ubuntu/crm-benchmark
   ```

3. Set up a virtual environment:
   ```
   cd /home/ubuntu/crm-benchmark
   python3 -m venv venv
   source venv/bin/activate
   ```

4. Install the application dependencies:
   ```
   pip install -r requirements.txt
   ```

5. Create a `.env` file with your configuration:
   ```
   cd website
   cp .env.example .env
   nano .env
   ```

   Update the environment variables with your settings.

6. Initialize the database:
   ```
   python init_db.py
   ```

## Step 4: Set Up Gunicorn

1. Install Gunicorn:
   ```
   pip install gunicorn
   ```

2. Create a systemd service file for Gunicorn:
   ```
   sudo nano /etc/systemd/system/crm-benchmark.service
   ```

3. Add the following content:
   ```
   [Unit]
   Description=Gunicorn instance to serve CRM AI Agent Benchmarking
   After=network.target

   [Service]
   User=ubuntu
   Group=www-data
   WorkingDirectory=/home/ubuntu/crm-benchmark/website
   Environment="PATH=/home/ubuntu/crm-benchmark/venv/bin"
   ExecStart=/home/ubuntu/crm-benchmark/venv/bin/gunicorn --workers 3 --bind unix:crm-benchmark.sock -m 007 app:app

   [Install]
   WantedBy=multi-user.target
   ```

4. Start and enable the service:
   ```
   sudo systemctl start crm-benchmark
   sudo systemctl enable crm-benchmark
   ```

## Step 5: Configure Nginx

1. Create an Nginx configuration file:
   ```
   sudo nano /etc/nginx/sites-available/crm-benchmark
   ```

2. Add the following content:
   ```
   server {
       listen 80;
       server_name your_domain.com www.your_domain.com;

       location / {
           include proxy_params;
           proxy_pass http://unix:/home/ubuntu/crm-benchmark/website/crm-benchmark.sock;
       }
   }
   ```

3. Enable the site:
   ```
   sudo ln -s /etc/nginx/sites-available/crm-benchmark /etc/nginx/sites-enabled
   ```

4. Test the Nginx configuration:
   ```
   sudo nginx -t
   ```

5. Restart Nginx:
   ```
   sudo systemctl restart nginx
   ```

## Step 6: Set Up HTTPS with Let's Encrypt (Optional but Recommended)

1. Install Certbot:
   ```
   sudo apt install -y certbot python3-certbot-nginx
   ```

2. Obtain and install an SSL certificate:
   ```
   sudo certbot --nginx -d your_domain.com -d www.your_domain.com
   ```

3. Follow the prompts to complete the setup and configure automatic renewal.

## Step 7: Verify Deployment

1. Visit your domain or server IP in a web browser
2. Verify that the application is running correctly
3. Test user registration and login
4. Test the API functionality

## Security Considerations

1. Update the SECRET_KEY in the .env file to a strong random string
2. Consider setting up a firewall (UFW is recommended for Ubuntu)
3. Set up regular backups of the database
4. Configure monitoring for the server

## Troubleshooting

- Check Gunicorn logs: `sudo journalctl -u crm-benchmark`
- Check Nginx logs: `sudo less /var/log/nginx/error.log`
- Verify file permissions
- Make sure all services are running

## Updating the Application

To update the application:

1. Pull the latest code:
   ```
   cd /home/ubuntu/crm-benchmark
   git pull
   ```

2. Activate the virtual environment:
   ```
   source venv/bin/activate
   ```

3. Update dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Restart the Gunicorn service:
   ```
   sudo systemctl restart crm-benchmark
   ``` 