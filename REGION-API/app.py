import asyncio
import time
import httpx
import json
import base64
import threading
from collections import defaultdict
from typing import Tuple, Dict, Any
from flask import Flask, request, jsonify
from flask_cors import CORS
from cachetools import TTLCache
from google.protobuf import json_format, message
from Crypto.Cipher import AES

# === Proto imports (must exist in your project) ===
from proto import FreeFire_pb2, main_pb2, AccountPersonalShow_pb2

# === Settings ===
MAIN_KEY = base64.b64decode('WWcmdGMlREV1aDYlWmNeOA==')
MAIN_IV = base64.b64decode('Nm95WkRyMjJFM3ljaGpNJQ==')
RELEASEVERSION = "OB55"
USERAGENT = "Dalvik/2.1.0 (Linux; U; Android 13; CPH2095 Build/RKQ1.211119.001)"
SUPPORTED_REGIONS = {"IND", "BR", "US", "SAC", "NA", "SG", "RU", "ID", "TW", "VN", "TH", "ME", "PK", "CIS", "BD", "EUROPE"}

# Regions we will try for /ban-check in order:
BANCHECK_REGIONS = ["IND", "BR", "BD"]

# === External JWT API ===
EXT_API_UID_PASS = "https://star-jwt-api1.lovable.app/api/public/token"

# === Flask App Setup ===
app = Flask(__name__)
CORS(app)
cache = TTLCache(maxsize=100, ttl=300)
cached_tokens: Dict[str, Dict[str, Any]] = defaultdict(dict)

# === Helper Functions ===
def pad(text: bytes) -> bytes:
    padding_length = AES.block_size - (len(text) % AES.block_size)
    return text + bytes([padding_length] * padding_length)

def aes_cbc_encrypt(key: bytes, iv: bytes, plaintext: bytes) -> bytes:
    aes = AES.new(key, AES.MODE_CBC, iv)
    return aes.encrypt(pad(plaintext))

def decode_protobuf(encoded_data: bytes, message_type: message.Message) -> message.Message:
    instance = message_type()
    instance.ParseFromString(encoded_data)
    return instance

async def json_to_proto(json_data: str, proto_message: message.Message) -> bytes:
    json_format.ParseDict(json.loads(json_data), proto_message)
    return proto_message.SerializeToString()

def get_account_credentials(region: str) -> str:
    r = region.upper()
    if r == "IND":
        return "uid=4218389302&password=NILAY-9LRRJQ7P3-NR-CODEX"
    elif r == "BD":
        return "uid=4218400521&password=BY_XRSUPER-JZRQ3RURQ-XRRRR"
    elif r in {"BR", "US", "SAC", "NA"}:
        return "uid=4218400521&password=BY_XRSUPER-JZRQ3RURQ-XRRRR"
    else:
        return "uid=4218400521&password=BY_XRSUPER-JZRQ3RURQ-XRRRR"


# ============================================================
# EXTERNAL API: UID + Password → JWT
# ============================================================
async def get_jwt_external(uid: str, password: str) -> str:
    """Call external API for a fresh JWT. Returns token string or None."""
    try:
        url = f"{EXT_API_UID_PASS}?uid={uid}&password={password}"
        async with httpx.AsyncClient(timeout=25.0) as client:
            r = await client.get(url)
            if r.status_code != 200:
                print(f"[EXT] HTTP {r.status_code}: {r.text[:200]}")
                return None
            data = r.json()
            return data.get("token")
    except Exception as e:
        print(f"[EXT] error: {e}")
        return None


# === Token Generation ===
async def get_access_token(account: str) -> Tuple[str, str]:
    url = "https://ffmconnect.live.gop.garenanow.com/oauth/guest/token/grant"
    payload = account + "&response_type=token&client_type=2&client_secret=2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3&client_id=100067"
    headers = {
        'User-Agent': USERAGENT,
        'Connection': "Keep-Alive",
        'Accept-Encoding': "gzip",
        'Content-Type': "application/x-www-form-urlencoded"
    }
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.post(url, data=payload, headers=headers)
        data = resp.json()
        return data.get("access_token", "0"), data.get("open_id", "0")


async def create_jwt(region: str):
    try:
        # ---- STEP 1: External API first ----
        account = get_account_credentials(region)
        # Parse "uid=X&password=Y"
        creds = dict(kv.split("=", 1) for kv in account.split("&"))
        ext_uid = creds.get("uid", "")
        ext_pass = creds.get("password", "")

        ext_token = await get_jwt_external(ext_uid, ext_pass)
        if ext_token:
            print(f"[{region}] External API token OK")
            # Decode JWT for region/server info
            try:
                import jwt as pyjwt
                decoded = pyjwt.decode(ext_token, options={"verify_signature": False})
                lock_region = decoded.get("lock_region", region)
            except Exception:
                lock_region = region

            cached_tokens[region] = {
                'token': f"Bearer {ext_token}",
                'region': lock_region,
                'server_url': "https://client.ind.freefiremobile.com" if lock_region == "IND"
                              else "https://clientbp.ggpolarbear.com",
                'expires_at': time.time() + 25200,
                'source': 'external'
            }
            return

        print(f"[{region}] External API failed, falling back to internal")

        # ---- STEP 2: Internal fallback ----
        token_val, open_id = await get_access_token(account)
        body = json.dumps({"open_id": open_id, "open_id_type": "4", "login_token": token_val, "orign_platform_type": "4"})
        proto_bytes = await json_to_proto(body, FreeFire_pb2.LoginReq())
        payload = aes_cbc_encrypt(MAIN_KEY, MAIN_IV, proto_bytes)
        url = "https://loginbp.ggblueshark.com/MajorLogin"
        headers = {
            'User-Agent': USERAGENT, 'Connection': "Keep-Alive", 'Accept-Encoding': "gzip",
            'Content-Type': "application/octet-stream", 'Expect': "100-continue",
            'X-Unity-Version': "2018.4.11f1", 'X-GA': "v1 1", 'ReleaseVersion': RELEASEVERSION
        }
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(url, data=payload, headers=headers)
            proto_resp = decode_protobuf(resp.content, FreeFire_pb2.LoginRes)
            msg = json.loads(json_format.MessageToJson(proto_resp))

            cached_tokens[region] = {
                'token': f"Bearer {msg.get('token','0')}",
                'region': msg.get('lockRegion','0'),
                'server_url': msg.get('serverUrl','0'),
                'expires_at': time.time() + 25200,
                'source': 'internal'
            }
    except Exception as e:
        cached_tokens[region] = {
            'error': str(e),
            'expires_at': 0
        }


async def initialize_tokens_for_regions(regions):
    tasks = [create_jwt(r) for r in regions]
    await asyncio.gather(*tasks)


async def _refresher_loop(regions):
    await initialize_tokens_for_regions(regions)
    while True:
        await asyncio.sleep(25200)
        await initialize_tokens_for_regions(regions)


def start_background_refresher(regions):
    def _runner():
        try:
            asyncio.run(_refresher_loop(regions))
        except Exception:
            pass
    t = threading.Thread(target=_runner, daemon=True)
    t.start()


async def get_token_info(region: str) -> Tuple[str, str, str]:
    info = cached_tokens.get(region)
    if info and info.get('expires_at', 0) > time.time() and 'token' in info and 'server_url' in info:
        return info['token'], info['region'], info['server_url']
    await create_jwt(region)
    info = cached_tokens.get(region, {})
    return info.get('token', ''), info.get('region', ''), info.get('server_url', '')


async def GetAccountInformation(uid, unk, region, endpoint):
    region = region.upper()
    if region not in SUPPORTED_REGIONS:
        raise ValueError(f"Unsupported region: {region}")
    payload = await json_to_proto(json.dumps({'a': uid, 'b': unk}), main_pb2.GetPlayerPersonalShow())
    data_enc = aes_cbc_encrypt(MAIN_KEY, MAIN_IV, payload)
    token, lock, server = await get_token_info(region)
    if not token or not server:
        raise RuntimeError(f"No token/server for region {region}: {cached_tokens.get(region)}")
    headers = {
        'User-Agent': USERAGENT, 'Connection': "Keep-Alive", 'Accept-Encoding': "gzip",
        'Content-Type': "application/octet-stream", 'Expect': "100-continue",
        'Authorization': token, 'X-Unity-Version': "2018.4.11f1", 'X-GA': "v1 1",
        'ReleaseVersion': RELEASEVERSION
    }
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.post(server + endpoint, data=data_enc, headers=headers)
        proto = decode_protobuf(resp.content, AccountPersonalShow_pb2.AccountPersonalShowInfo)
        return json.loads(json_format.MessageToJson(proto))


def format_response(data):
    return {
        "region": data.get("basicInfo", {}).get("region", ""),
        "nickname": data.get("basicInfo", {}).get("nickname", "")
    }


# === API Routes ===
@app.route('/player-info')
def get_account_info():
    region = request.args.get('region')
    uid = request.args.get('uid')
    if not uid or not region:
        return jsonify({"error": "Please provide UID and REGION."}), 400
    try:
        return_data = asyncio.run(GetAccountInformation(uid, "7", region, "/GetPlayerPersonalShow"))
        formatted = format_response(return_data)
        return jsonify(formatted), 200
    except Exception as e:
        return jsonify({"error": "Invalid UID or Region. Please check and try again.", "detail": str(e)}), 500


@app.route('/refresh', methods=['GET', 'POST'])
def refresh_tokens_endpoint():
    try:
        asyncio.run(initialize_tokens_for_regions(SUPPORTED_REGIONS))
        return jsonify({'message': 'Tokens refreshed for requested regions.'}), 200
    except Exception as e:
        return jsonify({'error': f'Refresh failed: {e}'}), 500


@app.route('/check')
def ban_check():
    uid = request.args.get('uid')
    if not uid:
        return jsonify({"error": "Please provide UID parameter."}), 400

    errors = {}
    for region in BANCHECK_REGIONS:
        try:
            data = asyncio.run(GetAccountInformation(uid, "7", region, "/GetPlayerPersonalShow"))
            formatted = format_response(data)
            return jsonify({
                "responding_region": region,
                "raw_api_response": data,
                "formatted_response": formatted
            }), 200
        except Exception as e:
            errors[region] = str(e)

    return jsonify({
        "error": "No regions returned a valid response for the UID.",
        "per_region_errors": errors
    }), 500


# === Startup ===
import sys

async def startup():
    print("[🚀] Initializing tokens...")
    await initialize_tokens_for_regions(SUPPORTED_REGIONS)
    start_background_refresher(SUPPORTED_REGIONS)
    print("[🚀] Startup complete")

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    print(f"[🚀] Starting on port {port} ...")
    try:
        asyncio.run(startup())
    except Exception as e:
        print(f"[⚠️] Startup warning: {e} — continuing without full initialization")
    app.run(host='0.0.0.0', port=port, debug=False)
