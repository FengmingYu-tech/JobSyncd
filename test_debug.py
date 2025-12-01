"""
测试调试工具的简单脚本
"""
import time
from debug_tool import workspace

def test_function(x, y):
    """测试函数"""
    workspace.update_variable("x", x, "test_function")
    workspace.update_variable("y", y, "test_function")
    result = x + y
    workspace.update_variable("result", result, "test_function")
    return result

def main():
    """主函数"""
    # 启动调试界面
    workspace.start()
    
    # 添加监视变量
    workspace.watch_variable("result")
    workspace.watch_variable("x")
    
    # 添加断点
    workspace.add_breakpoint("test_function")
    
    workspace._log("开始测试...")
    workspace.update_display()
    time.sleep(1)
    
    # 调用测试函数
    workspace._log("调用 test_function(5, 3)")
    result = test_function(5, 3)
    workspace.update_display()
    time.sleep(1)
    
    workspace._log(f"结果: {result}")
    workspace.update_display()
    time.sleep(2)
    
    # 停止调试界面
    workspace.stop()
    print("测试完成！")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        workspace.stop()
        print("\n测试中断")

