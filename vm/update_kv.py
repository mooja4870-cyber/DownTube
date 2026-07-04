#!/usr/bin/env python3
"""Cloudflare KV의 터널 주소(key=url)를 REST API로 기록/삭제한다.

node/wrangler 없이 동작하도록 표준 라이브러리만 사용. VM(도커) 배포용.

환경변수:
  CF_API_TOKEN   (필수) KV 편집 권한이 있는 Cloudflare API 토큰
  CF_ACCOUNT_ID  (선택) 기본값 내장
  CF_KV_NAMESPACE(선택) 기본값 내장

사용:
  python update_kv.py put https://xxxx.trycloudflare.com
  python update_kv.py delete
"""

import os
import sys
import urllib.error
import urllib.request

ACCOUNT_ID = os.environ.get("CF_ACCOUNT_ID", "09ed54fbf67ab75de38be2801e0b7d7d")
NAMESPACE = os.environ.get("CF_KV_NAMESPACE", "4e19a441a27e41f29fe540c6cd0114ba")
TOKEN = os.environ.get("CF_API_TOKEN", "")
API = (
    f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}"
    f"/storage/kv/namespaces/{NAMESPACE}/values/url"
)


def _request(method: str, data: bytes | None) -> int:
    req = urllib.request.Request(API, data=data, method=method)
    req.add_header("Authorization", f"Bearer {TOKEN}")
    if data is not None:
        req.add_header("Content-Type", "text/plain")
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            print(f"KV {method}: HTTP {resp.status}")
            return 0 if 200 <= resp.status < 300 else 1
    except urllib.error.HTTPError as e:
        print(f"KV {method} 실패: HTTP {e.code} {e.read().decode('utf-8', 'ignore')[:200]}")
        return 1
    except Exception as e:  # noqa: BLE001
        print(f"KV {method} 오류: {e}")
        return 1


def main() -> int:
    if not TOKEN:
        print("CF_API_TOKEN 환경변수가 필요합니다.")
        return 2
    action = sys.argv[1] if len(sys.argv) > 1 else ""
    if action == "put" and len(sys.argv) > 2:
        return _request("PUT", sys.argv[2].encode("utf-8"))
    if action == "delete":
        return _request("DELETE", None)
    print("사용법: update_kv.py put <URL> | delete")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
