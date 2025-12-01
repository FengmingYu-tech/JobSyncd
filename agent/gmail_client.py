import base64, os, re, datetime as dt
from typing import List, Dict, Optional
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from shared.config import GMAIL_CREDENTIALS_PATH, GMAIL_TOKEN_PATH

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# 环境变量：是否使用 Cursor Browser 进行 OAuth 认证
USE_CURSOR_BROWSER = os.getenv("USE_CURSOR_BROWSER", "false").lower() == "true"


def _creds():
    """
    获取 Gmail OAuth 凭据。
    
    如果设置了 USE_CURSOR_BROWSER=true 环境变量，将使用 Cursor Browser MCP 进行认证。
    否则使用传统的系统浏览器方式。
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))  # directory of this file
    # Use shared configuration or fallback to local paths
    cred_path = GMAIL_CREDENTIALS_PATH or os.path.join(base_dir, "credentials.json")
    token_path = GMAIL_TOKEN_PATH or os.path.join(base_dir, "token.json")

    creds = None
    # Check if we have a saved token first
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    # If no valid credentials, authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # google-authed client refreshes automatically when used
            pass
        else:
            # Need to authenticate with credentials.json
            if not os.path.exists(cred_path):
                raise FileNotFoundError(
                    f"credentials.json not found at {cred_path}. "
                    "Please download it from Google Cloud Console and place it in the agent directory."
                )
            
            # 检查是否使用 Cursor Browser
            if USE_CURSOR_BROWSER:
                print("🌐 使用 Cursor Browser 进行 OAuth 认证...")
                creds = _authenticate_with_cursor_browser(cred_path, token_path)
            else:
                creds = _authenticate_with_system_browser(cred_path, token_path)

    return creds


def _authenticate_with_system_browser(cred_path: str, token_path: str) -> Credentials:
    """使用系统默认浏览器进行 OAuth 认证（原有方式）"""
    flow = InstalledAppFlow.from_client_secrets_file(cred_path, SCOPES)

    # Try local server first (requires proper OAuth redirect URIs setup)
    ports_to_try = [8080, 49256, 8000]
    creds = None

    for port in ports_to_try:
        try:
            print(f"Attempting to start OAuth server on port {port}...")
            creds = flow.run_local_server(port=port, open_browser=True)
            print(f"✓ Successfully authenticated on port {port}")
            break
        except Exception as e:
            error_msg = str(e)
            if "OAuth 2.0" in error_msg or "redirect_uri" in error_msg:
                # OAuth policy error - redirect URI not configured
                print(f"✗ Port {port} failed due to OAuth configuration issue")
                print(f"  Error: {error_msg[:100]}")
            else:
                # Port in use or other error
                print(f"✗ Port {port} unavailable: {error_msg[:50]}")
            continue

    # If local server failed, fall back to console-based auth
    if not creds:
        print("\n" + "=" * 70)
        print("⚠ Could not use local server authentication.")
        print("Switching to manual authentication mode...")
        print("=" * 70)
        print("\n1. A browser window will open (or copy the URL that appears)")
        print("2. Sign in and authorize the app")
        print("3. You may see 'redirect_uri_mismatch' - that's OK!")
        print("4. Copy the code from the URL bar or the page")
        print("5. Paste it below\n")

        creds = flow.run_console()

    # Save the credentials for next time
    with open(token_path, "w") as f:
        f.write(creds.to_json())
    print(f"✓ Credentials saved to {token_path}")
    return creds


def _authenticate_with_cursor_browser(cred_path: str, token_path: str) -> Credentials:
    """
    使用 Cursor Browser MCP 进行 OAuth 认证。
    
    注意：这个函数需要在 Cursor agent 的上下文中运行，因为它依赖于
    Cursor Browser MCP 工具。如果在非 Cursor 环境中运行，将回退到系统浏览器。
    """
    try:
        from agent.browser_oauth import get_oauth_url_with_cursor_browser, complete_oauth_with_cursor_browser
        
        print("📋 步骤 1: 获取 OAuth 授权 URL...")
        oauth_info = get_oauth_url_with_cursor_browser(
            credentials_path=cred_path,
            scopes=SCOPES,
        )
        
        print("\n" + "=" * 70)
        print("🌐 请在 Cursor agent 中使用以下信息完成认证：")
        print("=" * 70)
        print(f"\n授权 URL: {oauth_info['auth_url']}")
        print(f"回调端口: {oauth_info['port']}")
        print("\n📝 在 Cursor agent 中执行以下操作：")
        print("1. 使用 browser_navigate 工具打开上面的授权 URL")
        print("2. 使用 browser_snapshot 查看页面状态")
        print("3. 使用 browser_click 和 browser_type 完成登录和授权")
        print("4. 等待认证完成...")
        print("=" * 70 + "\n")
        
        # 等待用户在 Cursor Browser 中完成认证
        print("⏳ 等待在 Cursor Browser 中完成认证...")
        print("   (认证完成后，系统将自动接收授权码)")
        
        creds = complete_oauth_with_cursor_browser(
            credentials_path=cred_path,
            scopes=SCOPES,
            auth_url=oauth_info['auth_url'],
            port=oauth_info['port'],
        )
        
        # Save the credentials for next time
        with open(token_path, "w") as f:
            f.write(creds.to_json())
        print(f"✓ Credentials saved to {token_path}")
        return creds
        
    except ImportError:
        print("⚠ Cursor Browser OAuth 模块未找到，回退到系统浏览器...")
        return _authenticate_with_system_browser(cred_path, token_path)
    except Exception as e:
        print(f"⚠ Cursor Browser 认证失败: {e}")
        print("回退到系统浏览器认证...")
        return _authenticate_with_system_browser(cred_path, token_path)


def _svc():
    return build("gmail", "v1", credentials=_creds(), cache_discovery=False)


def list_messages(
    query: str = "",
    max_results: int = 20,
    newer_than_days: Optional[int] = None,
    label_ids: Optional[List[str]] = None,
) -> List[Dict]:
    svc = _svc()
    q = query or ""
    if newer_than_days:
        q = (q + f" newer_than:{newer_than_days}d").strip()
    resp = (
        svc.users()
        .messages()
        .list(userId="me", q=q, maxResults=max_results, labelIds=label_ids or None)
        .execute()
    )
    return resp.get("messages", [])


def get_message(message_id: str) -> Dict:
    svc = _svc()
    return (
        svc.users().messages().get(userId="me", id=message_id, format="full").execute()
    )


def _decode_part(body) -> str:
    data = body.get("data")
    if not data:
        return ""
    return base64.urlsafe_b64decode(data.encode("utf-8")).decode(errors="ignore")


def _clean_html(html: str) -> str:
    """Clean HTML by removing styles, scripts, and extra whitespace."""
    if not html:
        return ""

    # Remove style blocks and their content
    html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE)
    # Remove script blocks and their content
    html = re.sub(
        r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE
    )
    # Remove HTML comments
    html = re.sub(r"<!--.*?-->", "", html, flags=re.DOTALL)
    # Remove all HTML tags
    html = re.sub(r"<[^>]+>", " ", html)
    # Decode common HTML entities
    html = (
        html.replace("&nbsp;", " ")
        .replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&quot;", '"')
    )
    # Collapse multiple spaces/newlines
    html = re.sub(r"\s+", " ", html)
    # Strip leading/trailing whitespace
    return html.strip()


def extract_text(payload: Dict) -> str:
    """Return best-effort plain text from MIME payload."""
    if not payload:
        return ""
    mime = payload.get("mimeType", "")
    body = payload.get("body", {})
    parts = payload.get("parts", [])

    # If single-part
    if not parts:
        if "text/plain" in mime:
            return _decode_part(body)
        if "text/html" in mime:
            html = _decode_part(body)
            return _clean_html(html)
        return ""

    # Multipart: prefer plain, fallback html
    text_chunks = []
    html_chunks = []
    stack = [payload]
    while stack:
        p = stack.pop()
        if p.get("parts"):
            stack.extend(p["parts"])
            continue
        mt = p.get("mimeType", "")
        b = p.get("body", {})
        if "text/plain" in mt:
            text_chunks.append(_decode_part(b))
        elif "text/html" in mt:
            html_chunks.append(_decode_part(b))

    if text_chunks:
        return "\n".join(text_chunks)
    if html_chunks:
        return _clean_html("\n".join(html_chunks))
    return ""


def message_summary(msg: Dict) -> Dict:
    headers = {
        h["name"].lower(): h["value"] for h in msg.get("payload", {}).get("headers", [])
    }
    snippet = msg.get("snippet", "")
    text = extract_text(msg.get("payload", {}))
    return {
        "id": msg["id"],
        "threadId": msg.get("threadId"),
        "from": headers.get("from"),
        "to": headers.get("to"),
        "subject": headers.get("subject"),
        "date": headers.get("date"),
        "snippet": snippet,
        "text": text[:50000],  # guardrails
    }
