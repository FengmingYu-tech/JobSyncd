"""
带调试界面的主程序
运行此文件可以启动可视化调试界面
"""
import asyncio
import sys
import os
import threading
import select
import termios
import tty
import signal

# Add parent directory to path to import from workflows
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from workflows.job_sync_workflow import JobSyncWorkflow
from shared.entry_points import run_workflow_with_error_handling
from debug_tool import workspace

# 全局变量用于键盘输入
_keyboard_enabled = False
_keyboard_thread = None

def handle_keyboard_input():
    """处理键盘输入（非阻塞）"""
    global _keyboard_enabled
    
    # 检查是否在交互式终端
    if not sys.stdin.isatty():
        workspace._log("⚠️  非交互式终端，键盘输入已禁用")
        workspace._log("💡 提示: 使用 Ctrl+C 中断，或在代码中调用 workspace.resume()")
        return
    
    try:
        old_settings = termios.tcgetattr(sys.stdin)
        tty.setcbreak(sys.stdin.fileno())
        _keyboard_enabled = True
        workspace._log("✅ 键盘输入已启用")
        workspace.update_display()
        
        while True:
            try:
                # 使用更短的超时时间，提高响应性
                if select.select([sys.stdin], [], [], 0.05)[0]:
                    key = sys.stdin.read(1)
                    
                    # 处理特殊字符（如 Ctrl+C）
                    if ord(key) == 3:  # Ctrl+C
                        workspace._log("⚠️  检测到 Ctrl+C")
                        workspace.stop()
                        os._exit(0)
                    
                    # 处理普通按键
                    if key == 'q' or key == 'Q':
                        workspace._log("用户退出调试模式 (按了 'q')")
                        workspace.stop()
                        os._exit(0)
                    elif key == 'c' or key == 'C':
                        workspace._log("用户继续执行 (按了 'c')")
                        workspace.resume()
                        workspace.update_display()
                    elif key == 's' or key == 'S':
                        workspace._log("用户单步执行 (按了 's')")
                        workspace.step()
                        workspace.update_display()
                    elif key == 'b' or key == 'B':
                        workspace.add_breakpoint("_call_gmail_mcp")
                        workspace._log("已添加断点: _call_gmail_mcp (按了 'b')")
                        workspace.update_display()
                    elif key == 'w' or key == 'W':
                        workspace.watch_variable("emails_count")
                        workspace.watch_variable("notion_result")
                        workspace._log("已监视变量: emails_count, notion_result (按了 'w')")
                        workspace.update_display()
                    elif key == 'p' or key == 'P':
                        workspace.pause()
                        workspace._log("用户暂停程序 (按了 'p')")
                        workspace.update_display()
            except (OSError, ValueError) as e:
                # 忽略读取错误，继续循环
                continue
                
    except (termios.error, AttributeError, OSError) as e:
        _keyboard_enabled = False
        workspace._log(f"⚠️  键盘输入不支持: {str(e)}")
        workspace._log("💡 提示: 使用 Ctrl+C 中断，或在代码中调用 workspace.resume()")
        workspace.update_display()
    except Exception as e:
        _keyboard_enabled = False
        workspace._log(f"⚠️  键盘输入错误: {str(e)}")
        workspace.update_display()
    finally:
        try:
            if 'old_settings' in locals():
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        except:
            pass

def setup_signal_handlers():
    """设置信号处理器作为备用方案"""
    def signal_handler(signum, frame):
        if signum == signal.SIGINT:
            workspace._log("⚠️  收到 SIGINT 信号 (Ctrl+C)")
            if workspace.paused:
                workspace._log("程序已暂停，继续执行...")
                workspace.resume()
                workspace.update_display()
            else:
                workspace._log("退出程序...")
                workspace.stop()
                os._exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)

async def daily_sync():
    """Main entry point for JobSync using MCP + LangGraph workflow"""
    workspace.update_variable("status", "Starting...", "daily_sync")
    workspace._log("🚀 Starting JobSyncd with MCP + LangGraph...")
    workspace.update_display()
    
    workflow = JobSyncWorkflow()
    workspace.update_variable("workflow", "JobSyncWorkflow instance", "daily_sync")
    workspace.update_variable("workflow.llm", str(workflow.llm), "daily_sync")
    workspace.update_variable("workflow.tools_count", len(workflow.tools), "daily_sync")
    workspace.update_display()
    
    workspace._log("📧 开始处理邮件...")
    result = await run_workflow_with_error_handling(workflow.run)
    
    workspace.update_variable("result", result, "daily_sync")
    workspace.update_variable("status", "Completed", "daily_sync")
    workspace._log("✅ 处理完成")
    workspace.update_display()
    
    return result

if __name__ == "__main__":
    # 启动调试界面
    workspace.start()
    
    # 设置信号处理器
    setup_signal_handlers()
    
    # 启动键盘输入处理线程
    _keyboard_thread = threading.Thread(target=handle_keyboard_input, daemon=True)
    _keyboard_thread.start()
    
    # 等待一下，让键盘输入线程初始化
    import time
    time.sleep(0.2)
    
    try:
        # 添加一些默认的监视变量
        workspace.watch_variable("status")
        workspace.watch_variable("result")
        
        # 可以添加一些默认断点
        # workspace.add_breakpoint("_call_gmail_mcp")
        # workspace.add_breakpoint("_call_notion_create")
        
        if _keyboard_enabled:
            workspace._log("💡 快捷键: 'c' 继续 | 's' 单步 | 'b' 断点 | 'w' 监视 | 'p' 暂停 | 'q' 退出")
        else:
            workspace._log("💡 键盘输入不可用，使用 Ctrl+C 中断，或在代码中调用 workspace.resume()")
            workspace._log("💡 代码控制: workspace.pause() / workspace.resume() / workspace.step()")
        
        workspace.update_display()
        
        # 运行主程序
        asyncio.run(daily_sync())
        
    except KeyboardInterrupt:
        workspace._log("⚠️  用户中断程序 (KeyboardInterrupt)")
        workspace.update_display()
    except Exception as e:
        workspace._log(f"❌ 程序错误: {str(e)}")
        import traceback
        workspace._log(traceback.format_exc())
        workspace.update_display()
    finally:
        workspace.stop()
        print("\n调试界面已关闭")

