"""
简化版调试主程序 - 使用代码控制，不依赖键盘输入
适合在 IDE 或非交互式终端中使用
"""
import asyncio
import sys
import os

# Add parent directory to path to import from workflows
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from workflows.job_sync_workflow import JobSyncWorkflow
from shared.entry_points import run_workflow_with_error_handling
from debug_tool import workspace

async def daily_sync():
    """Main entry point for JobSync using MCP + LangGraph workflow"""
    workspace.update_variable("status", "Starting...", "daily_sync")
    workspace._log("🚀 Starting JobSyncd with MCP + LangGraph...")
    workspace.update_display()
    
    # 示例：在关键位置添加暂停点
    # workspace.pause()  # 取消注释以在此处暂停
    
    workflow = JobSyncWorkflow()
    workspace.update_variable("workflow", "JobSyncWorkflow instance", "daily_sync")
    workspace.update_variable("workflow.llm", str(workflow.llm), "daily_sync")
    workspace.update_variable("workflow.tools_count", len(workflow.tools), "daily_sync")
    workspace.update_display()
    
    # 示例：在开始处理前暂停
    # workspace.pause()  # 取消注释以在此处暂停
    # workspace.resume()  # 或直接继续
    
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
    
    try:
        # 添加一些默认的监视变量
        workspace.watch_variable("status")
        workspace.watch_variable("result")
        workspace.watch_variable("emails_count")
        workspace.watch_variable("notion_result")
        
        # 添加断点（程序会在这些函数处自动暂停）
        workspace.add_breakpoint("_call_gmail_mcp")
        workspace.add_breakpoint("_call_notion_create")
        
        workspace._log("💡 代码控制模式")
        workspace._log("💡 在代码中使用 workspace.pause() / resume() / step() 控制执行")
        workspace._log("💡 已添加断点: _call_gmail_mcp, _call_notion_create")
        workspace.update_display()
        
        # 运行主程序
        asyncio.run(daily_sync())
        
    except KeyboardInterrupt:
        workspace._log("⚠️  用户中断程序")
        workspace.update_display()
    except Exception as e:
        workspace._log(f"❌ 程序错误: {str(e)}")
        import traceback
        workspace._log(traceback.format_exc())
        workspace.update_display()
    finally:
        workspace.stop()
        print("\n调试界面已关闭")

