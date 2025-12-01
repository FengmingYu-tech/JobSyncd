"""
带交互式调试界面的主程序（备用方案）
如果键盘输入不工作，使用这个版本
"""
import asyncio
import sys
import os
import threading
import queue

# Add parent directory to path to import from workflows
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from workflows.job_sync_workflow import JobSyncWorkflow
from shared.entry_points import run_workflow_with_error_handling
from debug_tool import workspace

# 命令队列
command_queue = queue.Queue()

def interactive_command_handler():
    """交互式命令处理器（使用 input()）"""
    workspace._log("💡 交互式模式：在另一个终端输入命令")
    workspace._log("💡 命令: resume, step, pause, quit")
    
    while True:
        try:
            # 注意：这个会在另一个线程中阻塞
            # 在实际使用中，你可能需要在主线程中处理
            pass
        except:
            break

def handle_commands_in_main():
    """在主线程中处理命令（非阻塞）"""
    import time
    
    workspace._log("💡 交互式调试模式")
    workspace._log("💡 在代码暂停时，可以在另一个终端运行以下命令：")
    workspace._log("   python -c \"from debug_tool import workspace; workspace.resume()\"")
    workspace._log("   python -c \"from debug_tool import workspace; workspace.step()\"")
    workspace._log("   python -c \"from debug_tool import workspace; workspace.pause()\"")
    workspace.update_display()
    
    # 创建一个简单的命令监听器
    def check_commands():
        while True:
            time.sleep(0.1)
            try:
                if not command_queue.empty():
                    cmd = command_queue.get_nowait()
                    if cmd == 'resume':
                        workspace.resume()
                    elif cmd == 'step':
                        workspace.step()
                    elif cmd == 'pause':
                        workspace.pause()
                    elif cmd == 'quit':
                        workspace.stop()
                        os._exit(0)
            except:
                pass
    
    thread = threading.Thread(target=check_commands, daemon=True)
    thread.start()

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
    
    # 启动命令处理器
    handle_commands_in_main()
    
    try:
        # 添加一些默认的监视变量
        workspace.watch_variable("status")
        workspace.watch_variable("result")
        
        # 可以添加一些默认断点
        # workspace.add_breakpoint("_call_gmail_mcp")
        # workspace.add_breakpoint("_call_notion_create")
        
        workspace.update_display()
        
        # 运行主程序
        asyncio.run(daily_sync())
        
    except KeyboardInterrupt:
        workspace._log("⚠️  用户中断程序")
    except Exception as e:
        workspace._log(f"❌ 程序错误: {str(e)}")
        import traceback
        workspace._log(traceback.format_exc())
    finally:
        workspace.stop()
        print("\n调试界面已关闭")

