# 快捷键修复说明

## 修复内容

### 1. 改进了键盘输入处理
- ✅ 添加了终端类型检测（`sys.stdin.isatty()`）
- ✅ 改进了错误处理和日志记录
- ✅ 添加了信号处理器作为备用方案
- ✅ 提高了响应性（缩短了睡眠时间）

### 2. 改进了暂停/继续逻辑
- ✅ 使用线程锁确保状态一致性
- ✅ 改进了暂停循环的响应性
- ✅ 添加了状态更新和显示刷新

### 3. 添加了备用方案
- ✅ 创建了 `main_debug_simple.py` - 使用代码控制，不依赖键盘
- ✅ 创建了 `test_keyboard.py` - 测试键盘输入是否可用
- ✅ 更新了使用指南

## 使用方法

### 方法 1: 标准版本（尝试键盘输入）

```bash
uv run python agent/main_debug.py
```

**如果键盘输入可用**：
- 按 'c' 继续
- 按 's' 单步执行
- 按 'b' 添加断点
- 按 'w' 监视变量
- 按 'p' 暂停
- 按 'q' 退出

**如果键盘输入不可用**（会显示警告）：
- 使用 Ctrl+C 控制（暂停时继续，运行时退出）
- 或在代码中使用 `workspace.resume()` 等方法

### 方法 2: 简化版本（代码控制，推荐用于 IDE）

```bash
uv run python agent/main_debug_simple.py
```

这个版本：
- 不依赖键盘输入
- 使用代码中的 `workspace.pause()` / `resume()` / `step()` 控制
- 已预配置断点和监视变量
- 适合在 IDE 或非交互式终端中使用

### 方法 3: 测试键盘输入

```bash
uv run python test_keyboard.py
```

这会测试你的终端是否支持键盘输入。

## 常见问题

### Q: 为什么快捷键不工作？

**A:** 可能的原因：
1. **IDE 集成终端**：大多数 IDE 的集成终端不是真正的交互式终端
2. **非交互式终端**：某些运行环境不支持 `termios`
3. **终端配置**：某些终端配置可能禁用了原始模式

### Q: 如何知道键盘输入是否可用？

**A:** 运行程序时，查看日志：
- 如果显示 "✅ 键盘输入已启用"，说明可用
- 如果显示 "⚠️ 键盘输入不支持" 或 "⚠️ 非交互式终端"，说明不可用

### Q: 键盘输入不可用时怎么办？

**A:** 有几种解决方案：

1. **使用代码控制**（最简单）：
   ```python
   from debug_tool import workspace
   workspace.pause()   # 暂停
   workspace.resume()  # 继续
   workspace.step()    # 单步
   ```

2. **使用系统终端**：
   - 不要在 IDE 中运行
   - 使用 Terminal.app 或 iTerm2
   - 运行：`uv run python agent/main_debug.py`

3. **使用 Ctrl+C**：
   - 程序暂停时，按 Ctrl+C 会继续
   - 程序运行时，按 Ctrl+C 会退出

4. **使用简化版本**：
   ```bash
   uv run python agent/main_debug_simple.py
   ```

## 改进的功能

### 1. 更好的错误处理
- 程序会自动检测键盘输入是否可用
- 如果不可用，会显示清晰的提示信息
- 不会因为键盘输入失败而崩溃

### 2. 信号处理器
- 添加了 SIGINT 信号处理器
- 当程序暂停时，Ctrl+C 会继续执行
- 当程序运行时，Ctrl+C 会退出

### 3. 状态同步
- 使用线程锁确保状态一致性
- 改进了暂停/继续的响应性
- 自动更新界面显示

## 推荐使用方式

### 在 IDE 中使用（如 Cursor、VS Code）
```bash
# 使用简化版本
uv run python agent/main_debug_simple.py
```

### 在系统终端中使用
```bash
# 使用标准版本（支持快捷键）
uv run python agent/main_debug.py
```

### 调试特定功能
在代码中添加控制点：
```python
from debug_tool import workspace

# 在关键位置添加
workspace.pause()  # 暂停，查看变量
# 检查变量后
workspace.resume()  # 继续
```

## 技术细节

### 键盘输入检测
程序会检查：
1. `sys.stdin.isatty()` - 是否为交互式终端
2. `termios` 是否可用
3. `select` 是否可用

### 备用方案
如果键盘输入不可用：
1. 使用信号处理器（Ctrl+C）
2. 使用代码控制（`workspace.resume()` 等）
3. 使用简化版本（`main_debug_simple.py`）

## 下一步

1. **测试键盘输入**：运行 `test_keyboard.py` 查看是否支持
2. **选择合适的版本**：
   - IDE 中 → 使用 `main_debug_simple.py`
   - 系统终端 → 使用 `main_debug.py`
3. **添加断点**：在代码中取消注释断点设置
4. **监视变量**：使用 `workspace.watch_variable()` 监视关键变量

