import time
from contextlib import contextmanager
from typing import TypedDict, cast
from urllib import parse

import requests

from .user_config import write_oauth_token

CLIENT_ID = 'da5e9528b63f1bd10fd8'


class DeviceFlowVerificationCodes(TypedDict):
    device_code: str
    user_code: str
    verification_uri: str
    expires_in: int
    interval: int


@contextmanager
def github_device_flow():
    verif_codes = _get_verification_codes()
    yield verif_codes
    access_token = _wait_for_authorization(verif_codes['device_code'], verif_codes['expires_in'], verif_codes['interval'])
    write_oauth_token(access_token)


def _get_verification_codes() -> DeviceFlowVerificationCodes:
    res = requests.post('https://github.com/login/device/code', {'client_id': CLIENT_ID})
    res.raise_for_status()
    r = dict(parse.parse_qsl(res.text))
    return {
        'device_code': r['device_code'],
        'user_code': r['user_code'],
        'verification_uri': r['verification_uri'],
        'expires_in': int(r['expires_in']),
        'interval': int(r['interval']),
    }


def _wait_for_authorization(device_code: str, expires_in: int, sleep_interval: int) -> str:
    time.sleep(sleep_interval)
    expires_in -= sleep_interval

    while expires_in > 0:
        try:
            return _get_access_token(device_code)
        except Exception as e:
            time.sleep(sleep_interval)
            expires_in -= sleep_interval
    else:
        raise Exception('Verification code expired')


def _get_access_token(device_code: str) -> str:
    res = requests.post('https://github.com/login/oauth/access_token', {
        'client_id': CLIENT_ID,
        'device_code': device_code,
        'grant_type': 'urn:ietf:params:oauth:grant-type:device_code'
    })
    res.raise_for_status()
    r = dict(parse.parse_qsl(res.text))

    if 'error' in r:
        raise Exception(r['error_description'], r['error'])

    access_token = r.get('access_token')
    assert(access_token)
    return access_token
