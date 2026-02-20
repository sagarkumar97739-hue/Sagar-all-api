import httpx
import time
import re
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, request, jsonify
from datetime import datetime
import asyncio
import data_pb2
import encode_id_clan_pb2

# ===================== CONFIG =====================
app = Flask(__name__)
freefire_version = "OB52"
key = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
iv = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])
jwt_tokens = {}  # Store tokens by region
# =================================================

# ===================== REGION CONFIG =====================
def get_region_credentials(region):
    r = region.upper()
    if r == "IND":
        return "uid=4218389302&password=NILAY-9LRRJQ7P3-NR-CODEX"
    elif r == "BD":
        return "uid=4218400521&password=BY_XRSUPER-JZRQ3RURQ-XRRRR"
    elif r in {"BR", "US", "SAC", "NA"}:
        return "uid=4218400521&password=BY_XRSUPER-JZRQ3RURQ-XRRRR"
    else:
        return "uid=4218400521&password=BY_XRSUPER-JZRQ3RURQ-XRRRR"

# ===================== ENCRYPT UID =====================
def Encrypt_ID(x):
    x = int(x)
    dec = [f'{i:02x}' for i in range(128, 256)]
    xxx = [f'{i:02x}' for i in range(0, 128)]

    parts = []
    while x > 0:
        parts.append(x % 128)
        x //= 128
    while len(parts) < 5:
        parts.append(0)
    parts.reverse()

    return ''.join(dec[parts[i]] if i > 0 else xxx[parts[i]] for i in range(5))

# ===================== AES ENCRYPT =====================
def encrypt_api(plain_text_hex):
    plain_text = bytes.fromhex(plain_text_hex)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return cipher.encrypt(pad(plain_text, 16)).hex()

# ===================== EMOTE ID EN/DE =====================
def Encrypt_id_emote(uid):
    result = []
    while uid > 0:
        byte = uid & 0x7F
        uid >>= 7
        if uid > 0:
            byte |= 0x80
        result.append(byte)
    return bytes(result).hex()

def Decrypt_id_emote(uidd):
    bytes_value = bytes.fromhex(uidd)
    r, shift = 0, 0
    for byte in bytes_value:
        r |= (byte & 0x7F) << shift
        if not (byte & 0x80):
            break
        shift += 7
    return r

# ===================== TIMESTAMP =====================
def convert_timestamp(ts):
    return datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

# ===================== JWT TOKEN =====================
async def get_jwt_token(region):
    global jwt_tokens
    credentials = get_region_credentials(region)
    
    # Determine API endpoint based on region
    if region.upper() == "IND":
        url = f"https://efpsrjqsrpgkxkzcfgor.supabase.co/functions/v1/jwt-api?api_key=SAGAR-FF&{credentials}"
    else:
        url = f"https://efpsrjqsrpgkxkzcfgor.supabase.co/functions/v1/jwt-api?api_key=SAGAR-FF&{credentials}"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    jwt_tokens[region.upper()] = data['token']
                    print(f"[+] JWT Token Updated for {region}: {data['token'][:50]}...")
                    return True
    except Exception as e:
        print(f"[-] JWT Token Error for {region}: {e}")
    return False

async def token_updater():
    regions = ["IND", "BD", "BR", "US", "SAC", "NA"]
    while True:
        for region in regions:
            await get_jwt_token(region)
            await asyncio.sleep(10)  # Small delay between regions
        await asyncio.sleep(8 * 3600)  # 8 hours

# ===================== CLAN INFO ROUTE (SYNC) =====================
@app.route('/info', methods=['GET'])
def get_clan_info():
    global jwt_tokens
    
    clan_id = request.args.get('clan_id')
    region = request.args.get('region', 'IND').upper()
    
    if not clan_id:
        return jsonify({"error": "clan_id is required"}), 400

    if region not in jwt_tokens or not jwt_tokens[region]:
        return jsonify({"error": f"JWT token for region {region} not ready. Try again in a few seconds."}), 503

    try:
        # Prepare Protobuf
        json_data = json.dumps({"1": int(clan_id), "2": 1})
        my_data = encode_id_clan_pb2.MyData()
        json_obj = json.loads(json_data)
        my_data.field1 = json_obj["1"]
        my_data.field2 = json_obj["2"]

        data_bytes = my_data.SerializeToString()
        encrypted_data = AES.new(key, AES.MODE_CBC, iv).encrypt(pad(data_bytes, 16))
        data_hex = encrypted_data.hex()

        # Determine API endpoint based on region
        if region == "IND":
            url = "https://client.ind.freefiremobile.com/GetClanInfoByClanID"
            host = "client.ind.freefiremobile.com"
        elif region == "BD":
            url = "https://client.bd.freefiremobile.com/GetClanInfoByClanID"
            host = "client.bd.freefiremobile.com"
        elif region in ["BR", "SAC"]:
            url = "https://client.br.freefiremobile.com/GetClanInfoByClanID"
            host = "client.br.freefiremobile.com"
        elif region in ["US", "NA"]:
            url = "https://client.na.freefiremobile.com/GetClanInfoByClanID"
            host = "client.na.freefiremobile.com"
        else:
            url = "https://client.ind.freefiremobile.com/GetClanInfoByClanID"
            host = "client.ind.freefiremobile.com"

        # Request headers
        headers = {
            "Expect": "100-continue",
            "Authorization": f"Bearer {jwt_tokens[region]}",
            "X-Unity-Version": "2018.4.11f1",
            "X-GA": "v1 1",
            "ReleaseVersion": freefire_version,
            "Content-Type": "application/octet-stream",
            "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 11; SM-A305F Build/RP1A.200720.012)",
            "Host": host,
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip"
        }

        # Synchronous HTTP using httpx
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, headers=headers, content=encrypted_data)

        if response.status_code != 200:
            return jsonify({"error": f"HTTP {response.status_code}", "body": response.text[:200]}), 500

        # Decrypt & Parse Response
        resp = data_pb2.response()
        resp.ParseFromString(response.content)

        def ts(x): return datetime.fromtimestamp(x).strftime("%Y-%m-%d %H:%M:%S")

        return jsonify({
            "id": resp.id,
            "clan_name": resp.special_code,
            "created_at": ts(resp.timestamp1),
            "updated_at": ts(resp.timestamp2),
            "last_active": ts(resp.last_active),
            "level": resp.level,
            "region": resp.region,
            "welcome_message": resp.welcome_message,
            "score": resp.score,
            "xp": resp.xp,
            "rank": resp.rank,
            "members_online": resp.guild_details.members_online,
            "total_members": resp.guild_details.total_members,
            "clan_id": resp.guild_details.clan_id,
            "error_code": resp.error_code,
            "status": "success",
            "requested_region": region
        })

    except Exception as e:
        return jsonify({"error": "Server error", "details": str(e)}), 500

# ===================== HEALTH CHECK =====================
@app.route('/health', methods=['GET'])
def health_check():
    regions_status = {}
    for region in ["IND", "BD", "BR", "US", "SAC", "NA"]:
        regions_status[region] = "ready" if region in jwt_tokens and jwt_tokens[region] else "not ready"
    
    return jsonify({
        "status": "running",
        "regions": regions_status,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/members', methods=['GET'])
def get_clan_members():
    clan_id = request.args.get('clan_id')
    region = request.args.get('region', 'IND').upper()
    page = int(request.args.get('page', 1))

    if not clan_id:
        return jsonify({"error": "clan_id is required"}), 400

    if region not in jwt_tokens or not jwt_tokens[region]:
        return jsonify({"error": f"JWT token for region {region} not ready"}), 503

    # -------- Build protobuf request --------
    req = get_clan_member_list_pb2.GetClanMemberListRequest()
    req.clan_id = int(clan_id)
    req.page = page

    raw = req.SerializeToString()

    cipher = AES.new(key, AES.MODE_CBC, iv)
    encrypted = cipher.encrypt(pad(raw, 16))

    # -------- Region endpoint --------
    if region == "IND":
        url = "https://client.ind.freefiremobile.com/GetClanMemberList"
        host = "client.ind.freefiremobile.com"
    elif region == "BD":
        url = "https://client.bd.freefiremobile.com/GetClanMemberList"
        host = "client.bd.freefiremobile.com"
    elif region in ["BR", "SAC"]:
        url = "https://client.br.freefiremobile.com/GetClanMemberList"
        host = "client.br.freefiremobile.com"
    else:
        url = "https://client.na.freefiremobile.com/GetClanMemberList"
        host = "client.na.freefiremobile.com"

    headers = {
        "Authorization": f"Bearer {jwt_tokens[region]}",
        "Content-Type": "application/octet-stream",
        "ReleaseVersion": freefire_version,
        "User-Agent": "Dalvik/2.1.0",
        "Host": host
    }

    with httpx.Client(timeout=30) as client:
        response = client.post(url, headers=headers, content=encrypted)

    if response.status_code != 200:
        return jsonify({"error": "http error", "code": response.status_code}), 500

    # -------- DECRYPT RESPONSE (VERY IMPORTANT) --------
    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted = unpad(cipher.decrypt(response.content), 16)

    resp = get_clan_member_list_pb2.GetClanMemberListResponse()
    resp.ParseFromString(decrypted)

    if resp.error_code != 0:
        return jsonify({
            "status": "failed",
            "error_code": resp.error_code
        }), 400

    # -------- Format output --------
    members = []
    for m in resp.members:
        members.append({
            "account_id": m.account_id,
            "nickname": m.nickname,
            "level": m.level,
            "role": m.role,
            "online": m.online,
            "rank_score": m.rank_score,
            "last_active": datetime.fromtimestamp(m.last_active).strftime("%Y-%m-%d %H:%M:%S")
        })

    return jsonify({
        "status": "success",
        "clan_id": int(clan_id),
        "page": resp.page,
        "total_members": resp.total_members,
        "members": members
    })

# ===================== STARTUP =====================
def start_background_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(token_updater())
    loop.run_forever()

if __name__ == '__main__':
    import sys
    import threading

    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    print(f"[🚀] Starting JWT-API on port {port} ...")

    threading.Thread(
        target=start_background_loop,
        daemon=True
    ).start()

    app.run(host='0.0.0.0', port=port, debug=False)
