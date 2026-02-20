SMS Bombing API

https://img.shields.io/badge/Python-3.7+-blue.svg
https://img.shields.io/badge/Flask-2.3.3-green.svg
https://img.shields.io/badge/License-MIT-orange.svg

A Flask-based API for sending OTP/SMS requests to multiple Bangladeshi services simultaneously. This tool is designed for educational and testing purposes only.

⚠️ Important Disclaimer

This tool is for educational purposes only. Misuse of this API for harassment, spam, or any illegal activities is strictly prohibited. The developers are not responsible for any misuse of this software. Always ensure you have proper authorization before testing any phone number.

Features

· Multi-threaded Execution: Send requests to multiple APIs simultaneously
· Scalable Architecture: Easily add or remove API endpoints
· RESTful API: Simple HTTP interface for integration
· Real-time Status: Monitor API health and performance
· Configurable Attempts: Control number of requests per API
· Error Handling: Comprehensive error reporting and logging

📋 Prerequisites

· Python 3.7 or higher
· pip (Python package manager)
· Internet connection

🚀 Installation

1. Clone the Repository

```bash
git clone https://github.com/yourusername/sms-bomb-api.git
cd sms-bomb-api
```

2. Install Dependencies

```bash
pip install -r requirements.txt
```

3. Run the Application

```bash
python app.py
```

For production deployment:

```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

📖 API Documentation

Base URL

```
http://localhost:5000
```

Endpoints

1. Start SMS Bombing

```
GET /devil?msisdn=PHONE_NUMBER
```

Parameters:

· msisdn (required): 11-digit Bangladeshi phone number (e.g., 01712345678)

Response:

```json
{
  "success": true,
  "message": "SMS bombing started successfully",
  "target": "01712345678",
  "total_apis": 12,
  "status": "running_in_background",
  "expected_requests": 36
}
```

2. Check Service Status

```
GET /devil/status
```

Response:

```json
{
  "service": "SMS Bombing API",
  "version": "1.0",
  "status": "active",
  "total_apis_configured": 12,
  "developer": "Team X Devil",
  "telegram": "https://t.me/GHOST_XOFC"
}
```

🛠️ Configuration

Supported APIs

The application currently supports 12 Bangladeshi services:

1. PBS OTP - Bangladesh Police Service
2. BD Tickets - Event ticketing platform
3. Shikho - Educational platform
4. DeepToPlay - Gaming platform
5. eCourier - Courier service
6. Sundarban Courier - Logistics service
7. Shomvob - Job marketplace
8. Bioscope - Streaming service
9. Grameenphone - Telecom operator
10. Kirei BD - E-commerce platform
11. GariBook - Transportation service
12. Chorki - Streaming service

Adding New APIs

To add a new API, modify the APIS list in app.py:

```python
{
    "name": "Service Name",
    "url": "https://api.example.com/endpoint",
    "method": "POST",  # or "GET"
    "headers": {
        "User-Agent": "Your User Agent",
        "Content-Type": "application/json"
    },
    "data_template": '{"phone":"{msisdn}"}'  # Use {msisdn} placeholder
}
```

⚙️ Configuration Options

Thread Pool Settings

Modify in bomb_sms() function:

```python
with ThreadPoolExecutor(max_workers=20) as executor:  # Adjust max_workers
```

Request Attempts

Change the attempts per API:

```python
threading.Thread(target=bomb_sms, args=(msisdn, 3), daemon=True).start()
```

🔧 Customization

1. Rate Limiting

Add delays between requests by modifying the timing in bomb_sms() function.

2. Logging

Add logging for debugging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

3. Proxy Support

Add proxy support to send_request() function:

```python
proxies = {
    'http': 'http://your-proxy:port',
    'https': 'https://your-proxy:port'
}
response = requests.post(url, headers=headers, data=data, proxies=proxies, timeout=10)
```

📊 Monitoring

Check Application Logs

```bash
# View real-time logs
tail -f app.log
```

Monitor Performance

Use the /devil/status endpoint to check:

· Service availability
· Number of configured APIs
· API version and status

🛡️ Security Considerations

1. Rate Limiting: Consider implementing rate limiting to prevent abuse
2. Authentication: Add API key authentication for production use
3. IP Whitelisting: Restrict access to trusted IP addresses
4. Request Validation: Validate phone numbers and request parameters
5. Logging: Maintain logs for audit trails

🐛 Troubleshooting

Common Issues

1. "Address already in use"
   ```bash
   # Kill process on port 5000
   sudo fuser -k 5000/tcp
   ```
2. Import errors
   ```bash
   # Reinstall dependencies
   pip install --force-reinstall -r requirements.txt
   ```
3. Connection errors
   · Check internet connection
   · Verify firewall settings
   · Ensure proxy settings are correct

Debug Mode

Run Flask in debug mode for detailed errors:

```python
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
```

📁 Project Structure

```
sms-bomb-api/
├── app.py              # Main Flask application
├── requirements.txt    # Python dependencies
├── README.md          # This file
├── config.py          # Configuration file (optional)
├── logs/              # Log directory
└── tests/             # Test cases
```

🤝 Contributing

1. Fork the repository
2. Create a feature branch (git checkout -b feature/AmazingFeature)
3. Commit your changes (git commit -m 'Add some AmazingFeature')
4. Push to the branch (git push origin feature/AmazingFeature)
5. Open a Pull Request

📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

⚠️ Legal Notice

This software is provided "as is" without warranty of any kind. The user assumes all responsibility for any legal consequences resulting from the use of this software. Always:

1. Obtain proper authorization before testing
2. Respect privacy and data protection laws
3. Comply with terms of service of targeted platforms
4. Use responsibly and ethically

📞 Contact

Developer: Team X Devil
Telegram: @GHOST_XOFC
For educational inquiries only.

---

Remember: With great power comes great responsibility. Use this tool ethically and legally.