"""
使用 Cursor Browser MCP 进行 OAuth 认证的辅助模块。

这个模块提供了使用 Cursor IDE 内置浏览器进行 OAuth 认证的功能，
替代传统的系统默认浏览器打开方式。
"""

import os
import json
import time
import urllib.parse
from typing import Optional, Dict, Any
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from google_auth_oauthlib.flow import InstalledAppFlow
from shared.config import GMAIL_CREDENTIALS_PATH


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """处理 OAuth 回调的 HTTP 服务器"""

    def __init__(self, *args, callback_url_queue=None, **kwargs):
        self.callback_url_queue = callback_url_queue
        super().__init__(*args, **kwargs)

    def do_GET(self):
        """处理 OAuth 回调"""
        # 构建完整的回调 URL（包括查询参数）
        callback_url = f"http://localhost:{self.server.server_port}{self.path}"
        
        parsed_path = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed_path.query)

        if "code" in query_params:
            if self.callback_url_queue:
                self.callback_url_queue.put(callback_url)

            # 发送成功页面
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(
                b"""
                <html>
                <head><title>认证成功</title></head>
                <body>
                <h1>认证成功！</h1>
                <p>您可以关闭此窗口并返回 Cursor。</p>
                <script>setTimeout(function(){window.close();}, 2000);</script>
                </body>
                </html>
                """
            )
        else:
            # 错误处理
            self.send_response(400)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            error = query_params.get("error", ["未知错误"])[0]
            self.wfile.write(
                f"""
                <html>
                <head><title>认证失败</title></head>
                <body>
                <h1>认证失败</h1>
                <p>错误: {error}</p>
                </body>
                </html>
                """.encode()
            )

    def log_message(self, format, *args):
        """禁用日志输出"""
        pass


def get_oauth_url_with_cursor_browser(
    credentials_path: Optional[str] = None,
    scopes: list = None,
    port: int = 8080,
) -> Dict[str, Any]:
    """
    使用 Cursor Browser MCP 获取 OAuth URL 并启动本地服务器。

    这个函数应该由 Cursor agent 调用，它会：
    1. 创建 OAuth flow
    2. 获取授权 URL
    3. 启动本地回调服务器
    4. 返回授权 URL 和服务器信息

    返回:
        dict: 包含 'auth_url', 'port', 'instructions' 的字典
    """
    if scopes is None:
        scopes = ["https://www.googleapis.com/auth/gmail.readonly"]

    if credentials_path is None:
        credentials_path = GMAIL_CREDENTIALS_PATH or os.path.join(
            os.path.dirname(__file__), "credentials.json"
        )

    if not os.path.exists(credentials_path):
        raise FileNotFoundError(
            f"credentials.json not found at {credentials_path}. "
            "Please download it from Google Cloud Console and place it in the agent directory."
        )

    # 创建 OAuth flow
    redirect_uri = f"http://localhost:{port}"
    flow = InstalledAppFlow.from_client_secrets_file(
        credentials_path, scopes, redirect_uri=redirect_uri
    )

    # 获取授权 URL
    auth_url, _ = flow.authorization_url(prompt="consent")

    return {
        "auth_url": auth_url,
        "port": port,
        "instructions": (
            f"请在 Cursor Browser 中打开以下 URL 进行认证：\n"
            f"{auth_url}\n\n"
            f"认证完成后，回调服务器将在端口 {port} 上接收授权码。"
        ),
    }


def complete_oauth_with_cursor_browser(
    credentials_path: Optional[str] = None,
    scopes: list = None,
    auth_url: str = None,
    port: int = 8080,
    timeout: int = 300,
) -> Any:
    """
    使用 Cursor Browser MCP 完成 OAuth 认证流程。

    这个函数应该由 Cursor agent 调用，它会：
    1. 启动本地回调服务器
    2. 在 Cursor Browser 中打开授权 URL
    3. 等待用户完成认证
    4. 接收授权码并交换 token

    参数:
        credentials_path: credentials.json 文件路径
        scopes: OAuth 作用域列表
        auth_url: 授权 URL（如果已获取）
        port: 回调服务器端口
        timeout: 超时时间（秒）

    返回:
        Credentials: Google OAuth 凭据对象
    """
    import queue

    if scopes is None:
        scopes = ["https://www.googleapis.com/auth/gmail.readonly"]

    if credentials_path is None:
        credentials_path = GMAIL_CREDENTIALS_PATH or os.path.join(
            os.path.dirname(__file__), "credentials.json"
        )

    if not os.path.exists(credentials_path):
        raise FileNotFoundError(
            f"credentials.json not found at {credentials_path}."
        )

    # 创建 OAuth flow
    redirect_uri = f"http://localhost:{port}"
    flow = InstalledAppFlow.from_client_secrets_file(
        credentials_path, scopes, redirect_uri=redirect_uri
    )

    # 如果没有提供 auth_url，先获取
    if auth_url is None:
        auth_url, _ = flow.authorization_url(prompt="consent")

    # 创建队列用于接收完整的回调 URL
    callback_url_queue = queue.Queue()

    # 启动回调服务器
    def create_handler(queue):
        def handler(*args, **kwargs):
            return OAuthCallbackHandler(*args, callback_url_queue=queue, **kwargs)

        return handler

    server = HTTPServer(("localhost", port), create_handler(callback_url_queue))
    server_thread = Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    redirect_uri = f"http://localhost:{port}"
    print(f"✓ 回调服务器已启动在端口 {port}")
    print(f"✓ 回调 URI: {redirect_uri}")
    print(f"✓ 请在 Cursor Browser 中打开以下 URL：\n{auth_url}\n")

    # 等待回调 URL（这里需要 Cursor agent 在浏览器中打开 URL）
    try:
        callback_url = callback_url_queue.get(timeout=timeout)
        print(f"✓ 收到回调，正在交换 token...")

        # 使用完整的回调 URL 获取 token
        # fetch_token 需要完整的 authorization_response URL
        flow.fetch_token(authorization_response=callback_url)
        creds = flow.credentials

        print("✓ OAuth 认证成功！")
        return creds

    except queue.Empty:
        raise TimeoutError(
            f"OAuth 认证超时（{timeout}秒）。请确保在 Cursor Browser 中完成了认证。"
        )
    finally:
        server.shutdown()
        server_thread.join(timeout=1)


# 供 Cursor agent 使用的工具函数
def setup_cursor_browser_oauth() -> Dict[str, str]:
    """
    设置 Cursor Browser OAuth 流程。

    这个函数返回需要在 Cursor agent 中执行的步骤说明。
    返回的字典包含可以在 Cursor Browser MCP 中使用的信息。
    """
    try:
        result = get_oauth_url_with_cursor_browser()
        return {
            "status": "ready",
            "auth_url": result["auth_url"],
            "port": str(result["port"]),
            "next_step": (
                "请在 Cursor agent 中使用 browser_navigate 工具打开 auth_url，"
                "然后使用 browser_snapshot 监控页面状态，"
                "最后使用 browser_click 完成认证流程。"
            ),
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
        }

