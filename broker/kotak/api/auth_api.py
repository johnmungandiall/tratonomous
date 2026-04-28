import base64
import json
import os

import httpx

from utils.httpx_client import get_httpx_client
from utils.logging import get_logger

# Initialize logger
logger = get_logger(__name__)


def authenticate_broker(mobile_number, totp, mpin):
    """
    Authenticate with Kotak using OAuth2 + TOTP + MPIN flow.

    Steps:
    0. Session init: OAuth2 client_credentials → bearer_token
    1. Login with TOTP to get View token and sid
    2. Validate with MPIN to get Trading token, sid, and serverId

    Args:
        mobile_number: Mobile number with +91 prefix
        totp: 6-digit TOTP from authenticator app
        mpin: 6-digit trading MPIN

    Returns:
        Tuple of (auth_string, error_message)
        auth_string format: "trading_token:::trading_sid:::base_url:::bearer_token:::server_id"
    """
    try:
        logger.info("Starting Kotak authentication flow")

        from utils.config import get_broker_api_key, get_broker_api_secret

        consumer_key = get_broker_api_key()
        consumer_secret = get_broker_api_secret()

        if not consumer_key:
            logger.error("BROKER_API_KEY (consumer_key/UCC) is not configured")
            return None, "BROKER_API_KEY is required in .env file"

        if not consumer_secret:
            logger.error("BROKER_API_SECRET (consumer_secret) is not configured")
            return None, "BROKER_API_SECRET is required in .env file"

        # Ensure mobile number has +91 prefix
        mobile_number = mobile_number.strip()
        mobile_number = mobile_number.replace("+91", "").replace(" ", "")
        if mobile_number.startswith("91") and len(mobile_number) == 12:
            mobile_number = mobile_number[2:]
        mobile_number = f"+91{mobile_number}"

        client = get_httpx_client()

        # Step 0: OAuth2 session init to get bearer_token
        base64_credentials = base64.b64encode(
            f"{consumer_key}:{consumer_secret}".encode("ascii")
        ).decode("ascii")

        oauth_headers = {
            "Authorization": f"Basic {base64_credentials}",
            "Content-Type": "application/json",
        }

        logger.info("Step 0: OAuth2 session init")
        oauth_response = client.post(
            "https://napi.kotaksecurities.com/oauth2/token",
            headers=oauth_headers,
            content=json.dumps({"grant_type": "client_credentials"}),
        )

        logger.debug(f"OAuth2 Response Status: {oauth_response.status_code}")
        logger.debug(f"OAuth2 Response: {oauth_response.text}")

        oauth_data = json.loads(oauth_response.text)

        if "access_token" not in oauth_data:
            error_msg = oauth_data.get("error_description", oauth_data.get("error", "OAuth2 session init failed"))
            logger.error(f"OAuth2 session init failed: {oauth_data}")
            return None, f"OAuth2 Error: {error_msg}"

        bearer_token = oauth_data["access_token"]
        logger.info("OAuth2 session init successful, got bearer_token")

        # Step 1: Login with TOTP
        payload = json.dumps({"mobileNumber": mobile_number, "ucc": consumer_key, "totp": totp})

        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "neo-fin-key": "neotradeapi",
            "Content-Type": "application/json",
        }

        logger.debug(f"TOTP Login Request - Mobile: {mobile_number[:5]}***, UCC: {consumer_key}")

        response = client.post(
            "https://mis.kotaksecurities.com/login/1.0/tradeApiLogin",
            headers=headers,
            content=payload,
        )

        logger.debug(f"TOTP Login Response Status: {response.status_code}")
        logger.debug(f"TOTP Login Response: {response.text}")

        data_dict = json.loads(response.text)

        if "data" not in data_dict or data_dict.get("data", {}).get("status") != "success":
            error_msg = data_dict.get("errMsg", data_dict.get("message", "TOTP login failed"))
            logger.error(f"TOTP Login Failed - Response: {data_dict}")
            return None, f"TOTP Login Error: {error_msg}"

        view_token = data_dict["data"]["token"]
        view_sid = data_dict["data"]["sid"]

        logger.info("TOTP Login successful, proceeding with MPIN validation")

        # Step 2: Validate with MPIN
        payload = json.dumps({"mpin": mpin})

        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "neo-fin-key": "neotradeapi",
            "sid": view_sid,
            "Auth": view_token,
            "Content-Type": "application/json",
        }

        logger.debug("MPIN Validation Request initiated")

        response = client.post(
            "https://mis.kotaksecurities.com/login/1.0/tradeApiValidate",
            headers=headers,
            content=payload,
        )

        logger.debug(f"MPIN Validation Response Status: {response.status_code}")
        logger.debug(f"MPIN Validation Response: {response.text}")

        data_dict = json.loads(response.text)

        if "data" not in data_dict or data_dict.get("data", {}).get("status") != "success":
            error_msg = data_dict.get("errMsg", data_dict.get("message", "MPIN validation failed"))
            logger.error(f"MPIN Validation Failed - Response: {data_dict}")
            return None, f"MPIN Validation Error: {error_msg}"

        trading_token = data_dict["data"]["token"]
        trading_sid = data_dict["data"]["sid"]
        base_url = data_dict["data"].get("baseUrl", "")
        server_id = data_dict["data"].get("hsServerId", "")

        if not base_url:
            logger.warning("baseUrl not found in MPIN validation response")

        if not server_id:
            logger.warning("hsServerId not found in MPIN validation response")

        logger.info("Kotak authentication completed successfully")
        logger.debug(f"Base URL: {base_url}, Server ID: {server_id}")

        # Auth string: trading_token:::trading_sid:::base_url:::bearer_token:::server_id
        auth_string = f"{trading_token}:::{trading_sid}:::{base_url}:::{bearer_token}:::{server_id}"

        return auth_string, None

    except KeyError as e:
        logger.error(f"Missing expected field in API response: {str(e)}")
        return None, f"Missing expected field in API response: {str(e)}"
    except httpx.HTTPError as e:
        logger.error(f"HTTP request failed: {str(e)}")
        return None, f"HTTP request failed: {str(e)}"
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response: {str(e)}")
        return None, f"Failed to parse JSON response: {str(e)}"
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        return None, f"Authentication error: {str(e)}"
