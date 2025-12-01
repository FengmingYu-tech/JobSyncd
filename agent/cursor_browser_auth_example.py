"""
示例：如何在 Cursor Agent 中使用 Cursor Browser 进行 OAuth 认证

这个脚本展示了在 Cursor agent 中完成 Gmail OAuth 认证的完整流程。
"""

import os
import sys

# 设置使用 Cursor Browser
os.environ["USE_CURSOR_BROWSER"] = "true"

# 添加父目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agent.browser_oauth import get_oauth_url_with_cursor_browser, complete_oauth_with_cursor_browser
from shared.config import GMAIL_CREDENTIALS_PATH


def main():
    """
    在 Cursor Agent 中执行以下步骤：
    
    1. 运行此脚本获取 OAuth URL
    2. 在 Cursor agent 中使用 browser_navigate 打开 URL
    3. 使用 browser_snapshot, browser_click, browser_type 完成认证
    4. 等待认证完成
    """
    print("=" * 70)
    print("Cursor Browser OAuth 认证示例")
    print("=" * 70)
    
    # 获取 OAuth URL
    try:
        oauth_info = get_oauth_url_with_cursor_browser()
        
        print("\n✅ OAuth URL 已生成")
        print(f"\n授权 URL: {oauth_info['auth_url']}")
        print(f"回调端口: {oauth_info['port']}")
        
        print("\n" + "=" * 70)
        print("📝 在 Cursor Agent 中执行以下操作：")
        print("=" * 70)
        print("\n1. 使用 browser_navigate 工具：")
        print(f'   browser_navigate(url="{oauth_info["auth_url"]}")')
        print("\n2. 使用 browser_snapshot 查看页面：")
        print("   browser_snapshot()")
        print("\n3. 根据页面内容完成登录和授权：")
        print("   - 使用 browser_type 输入邮箱")
        print("   - 使用 browser_click 点击按钮")
        print("   - 使用 browser_type 输入密码（如需要）")
        print("   - 继续操作直到看到成功页面")
        print("\n4. 认证完成后，运行以下代码完成 token 交换：")
        print(f'   complete_oauth_with_cursor_browser(auth_url="{oauth_info["auth_url"]}")')
        print("=" * 70)
        
        # 等待用户确认
        input("\n按 Enter 键开始等待认证完成（或 Ctrl+C 取消）...")
        
        # 完成认证
        print("\n⏳ 等待认证完成...")
        creds = complete_oauth_with_cursor_browser(
            auth_url=oauth_info['auth_url'],
            port=oauth_info['port'],
        )
        
        # 保存凭据
        token_path = os.path.join(os.path.dirname(__file__), "token.json")
        with open(token_path, "w") as f:
            f.write(creds.to_json())
        
        print(f"\n✅ 认证成功！凭据已保存到: {token_path}")
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()





