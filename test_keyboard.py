"""
测试键盘输入是否工作
"""
import sys
import select
import termios
import tty

print("测试键盘输入...")
print("按任意键测试（5秒超时）")

try:
    if not sys.stdin.isatty():
        print("❌ 非交互式终端")
        sys.exit(1)
    
    old_settings = termios.tcgetattr(sys.stdin)
    tty.setcbreak(sys.stdin.fileno())
    
    print("✅ 终端设置成功")
    print("等待按键...")
    
    if select.select([sys.stdin], [], [], 5)[0]:
        key = sys.stdin.read(1)
        print(f"✅ 成功读取按键: '{key}' (ASCII: {ord(key)})")
    else:
        print("❌ 超时：没有检测到按键")
    
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
    
except termios.error as e:
    print(f"❌ termios 错误: {e}")
except AttributeError as e:
    print(f"❌ 属性错误: {e}")
except Exception as e:
    print(f"❌ 其他错误: {e}")
finally:
    try:
        if 'old_settings' in locals():
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
    except:
        pass

print("\n测试完成")

