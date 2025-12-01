"""
调试工具 - 类似 MATLAB Workspace 的可视化调试界面
支持变量监视、调用栈跟踪、断点等功能
"""
import functools
import time
import inspect
from typing import Any, Dict, List, Optional, Callable
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from rich.layout import Layout
from rich.text import Text
from rich.prompt import Prompt
from collections import deque
import threading
import json

class Breakpoint:
    """断点类"""
    def __init__(self, func_name: str, condition: Optional[Callable] = None):
        self.func_name = func_name
        self.condition = condition
        self.hit_count = 0
        self.enabled = True
        
    def check(self, func_name: str, *args, **kwargs) -> bool:
        """检查是否应该触发断点"""
        if not self.enabled:
            return False
        if self.func_name == func_name or self.func_name in func_name:
            if self.condition is None:
                return True
            try:
                return self.condition(*args, **kwargs)
            except:
                return True
        return False

class DebugWorkspace:
    """类似 MATLAB Workspace 的调试工具"""
    
    def __init__(self):
        self.console = Console()
        self.variables = {}
        self.watched_variables = set()  # 被监视的变量
        self.call_stack = deque(maxlen=30)
        self.execution_log = deque(maxlen=100)
        self.current_function = None
        self.current_file = None
        self.current_line = None
        self.live = None
        self.layout = None
        self.breakpoints: List[Breakpoint] = []
        self.paused = False
        self.step_mode = False
        self._lock = threading.Lock()
        
    def add_breakpoint(self, func_name: str, condition: Optional[Callable] = None):
        """添加断点"""
        bp = Breakpoint(func_name, condition)
        self.breakpoints.append(bp)
        self._log(f"添加断点: {func_name}")
        
    def remove_breakpoint(self, func_name: str):
        """移除断点"""
        self.breakpoints = [bp for bp in self.breakpoints if bp.func_name != func_name]
        self._log(f"移除断点: {func_name}")
        
    def toggle_breakpoint(self, func_name: str):
        """切换断点状态"""
        for bp in self.breakpoints:
            if bp.func_name == func_name:
                bp.enabled = not bp.enabled
                self._log(f"切换断点: {func_name} -> {'启用' if bp.enabled else '禁用'}")
                return
                
    def watch_variable(self, name: str):
        """监视变量"""
        self.watched_variables.add(name)
        self._log(f"开始监视变量: {name}")
        
    def unwatch_variable(self, name: str):
        """取消监视变量"""
        self.watched_variables.discard(name)
        self._log(f"停止监视变量: {name}")
        
    def update_variable(self, name: str, value: Any, location: str = ""):
        """更新变量值"""
        with self._lock:
            old_value = self.variables.get(name, {}).get('value')
            self.variables[name] = {
                'value': value,
                'type': type(value).__name__,
                'location': location,
                'timestamp': time.time(),
                'changed': old_value != value
            }
            
            # 如果变量被监视且值发生变化，记录日志
            if name in self.watched_variables and old_value != value:
                self._log(f"⚠️ 监视变量变化: {name} = {str(value)[:50]}")
            else:
                self._log(f"变量更新: {name} = {str(value)[:50]}")
        
    def push_call(self, func_name: str, args: Dict, kwargs: Dict, file: str = "", line: int = 0):
        """记录函数调用"""
        with self._lock:
            self.call_stack.append({
                'function': func_name,
                'args': args,
                'kwargs': kwargs,
                'file': file,
                'line': line,
                'time': time.time()
            })
            self.current_function = func_name
            self.current_file = file
            self.current_line = line
            self._log(f"→ 调用函数: {func_name}")
            
            # 检查断点
            for bp in self.breakpoints:
                if bp.check(func_name, *args.values() if args else [], **kwargs):
                    bp.hit_count += 1
                    self._log(f"🔴 断点触发: {func_name} (命中 {bp.hit_count} 次)")
                    self.pause()
                    break
        
    def pop_call(self, func_name: str, result: Any = None):
        """记录函数返回"""
        with self._lock:
            if self.call_stack:
                self.call_stack.pop()
            if self.call_stack:
                self.current_function = self.call_stack[-1]['function']
                self.current_file = self.call_stack[-1].get('file', '')
                self.current_line = self.call_stack[-1].get('line', 0)
            else:
                self.current_function = None
                self.current_file = None
                self.current_line = None
            self._log(f"← 函数返回: {func_name}")
            
    def pause(self):
        """暂停执行"""
        with self._lock:
            self.paused = True
            self.step_mode = False
        self._log("⏸️  程序已暂停 (按 'c' 继续, 's' 单步执行, 'p' 暂停, 'q' 退出)")
        self.update_display()
        
    def resume(self):
        """继续执行"""
        with self._lock:
            was_paused = self.paused
            self.paused = False
            self.step_mode = False
        if was_paused:
            self._log("▶️  程序继续执行")
            self.update_display()
        
    def step(self):
        """单步执行"""
        with self._lock:
            self.step_mode = True
            self.paused = False
        self._log("👣 单步执行模式")
        self.update_display()
        
    def _log(self, message: str):
        """记录日志"""
        with self._lock:
            self.execution_log.append({
                'message': message,
                'time': time.time()
            })
        
    def create_layout(self):
        """创建布局"""
        layout = Layout()
        
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=4)
        )
        
        layout["main"].split_row(
            Layout(name="left"),
            Layout(name="right")
        )
        
        layout["left"].split_column(
            Layout(name="variables", ratio=2),
            Layout(name="watched", ratio=1),
            Layout(name="call_stack", ratio=2)
        )
        
        layout["right"].split_column(
            Layout(name="execution", ratio=3),
            Layout(name="current", ratio=1),
            Layout(name="breakpoints", ratio=1)
        )
        
        return layout
        
    def render_variables(self):
        """渲染变量表格"""
        table = Table(title="变量 (Variables)", show_header=True, header_style="bold magenta", show_lines=True)
        table.add_column("名称", style="cyan", width=20)
        table.add_column("类型", style="green", width=12)
        table.add_column("值", style="yellow", overflow="fold")
        table.add_column("位置", style="blue", width=20)
        
        if not self.variables:
            table.add_row("(无)", "", "", "")
        else:
            for name, info in sorted(self.variables.items()):
                value_str = str(info['value'])
                if len(value_str) > 60:
                    value_str = value_str[:57] + "..."
                
                # 标记变化的变量
                style = "bold yellow" if info.get('changed', False) else "yellow"
                table.add_row(
                    name,
                    info['type'],
                    Text(value_str, style=style),
                    info['location']
                )
        
        return Panel(table, title="Workspace Variables")
        
    def render_watched(self):
        """渲染监视变量"""
        table = Table(title="监视变量 (Watched)", show_header=True, header_style="bold cyan")
        table.add_column("变量名", style="green")
        table.add_column("当前值", style="yellow", overflow="fold")
        
        if not self.watched_variables:
            table.add_row("(无监视变量)", "")
        else:
            for name in sorted(self.watched_variables):
                if name in self.variables:
                    value = str(self.variables[name]['value'])
                    if len(value) > 40:
                        value = value[:37] + "..."
                    table.add_row(name, value)
                else:
                    table.add_row(name, "(未定义)")
        
        return Panel(table)
        
    def render_call_stack(self):
        """渲染调用栈"""
        table = Table(title="调用栈 (Call Stack)", show_header=True, header_style="bold cyan", show_lines=True)
        table.add_column("#", style="dim", width=3)
        table.add_column("函数", style="green")
        table.add_column("位置", style="blue", width=25)
        
        if not self.call_stack:
            table.add_row("0", "(无)", "")
        else:
            for i, call in enumerate(reversed(self.call_stack)):
                file_info = call.get('file', '')
                if file_info:
                    file_info = file_info.split('/')[-1]  # 只显示文件名
                line_info = f":{call.get('line', 0)}" if call.get('line') else ""
                location = f"{file_info}{line_info}"
                table.add_row(str(i), call['function'], location)
        
        return Panel(table)
        
    def render_execution_log(self):
        """渲染执行日志"""
        text = Text()
        for log in list(self.execution_log)[-30:]:
            timestamp = time.strftime('%H:%M:%S', time.localtime(log['time']))
            text.append(f"[{timestamp}] ", style="dim")
            
            # 根据消息类型设置样式
            msg = log['message']
            if "断点" in msg or "🔴" in msg:
                text.append(msg + "\n", style="bold red")
            elif "暂停" in msg or "⏸️" in msg:
                text.append(msg + "\n", style="bold yellow")
            elif "监视变量" in msg or "⚠️" in msg:
                text.append(msg + "\n", style="bold magenta")
            elif "调用" in msg or "→" in msg:
                text.append(msg + "\n", style="cyan")
            elif "返回" in msg or "←" in msg:
                text.append(msg + "\n", style="green")
            else:
                text.append(msg + "\n", style="white")
        
        return Panel(text, title="执行日志 (Execution Log)")
        
    def render_current(self):
        """渲染当前状态"""
        current_text = Text()
        current_text.append("当前函数: ", style="bold")
        current_text.append(self.current_function or "无", style="green")
        
        if self.current_file:
            current_text.append("\n文件: ", style="bold")
            current_text.append(self.current_file.split('/')[-1], style="cyan")
            if self.current_line:
                current_text.append(f":{self.current_line}", style="dim")
        
        current_text.append("\n\n变量数量: ", style="bold")
        current_text.append(str(len(self.variables)), style="cyan")
        current_text.append("\n调用深度: ", style="bold")
        current_text.append(str(len(self.call_stack)), style="yellow")
        
        if self.paused:
            current_text.append("\n\n状态: ", style="bold")
            current_text.append("⏸️ 已暂停", style="bold red")
        elif self.step_mode:
            current_text.append("\n\n状态: ", style="bold")
            current_text.append("👣 单步执行", style="bold yellow")
        else:
            current_text.append("\n\n状态: ", style="bold")
            current_text.append("▶️ 运行中", style="bold green")
        
        return Panel(current_text, title="当前状态 (Current State)")
        
    def render_breakpoints(self):
        """渲染断点列表"""
        table = Table(title="断点 (Breakpoints)", show_header=True, header_style="bold red")
        table.add_column("函数", style="green")
        table.add_column("状态", style="yellow")
        table.add_column("命中", style="cyan")
        
        if not self.breakpoints:
            table.add_row("(无断点)", "", "")
        else:
            for bp in self.breakpoints:
                status = "✓ 启用" if bp.enabled else "✗ 禁用"
                table.add_row(bp.func_name, status, str(bp.hit_count))
        
        return Panel(table)
        
    def render_header(self):
        """渲染头部"""
        header = Text("🔍 JobSync 调试工作区 (Debug Workspace)", style="bold white on blue")
        return Panel(header, height=3)
        
    def render_footer(self):
        """渲染底部"""
        footer_text = Text()
        footer_text.append("快捷键: ", style="bold")
        footer_text.append("'c' 继续 | ", style="cyan")
        footer_text.append("'s' 单步 | ", style="yellow")
        footer_text.append("'b <函数名>' 添加断点 | ", style="red")
        footer_text.append("'w <变量名>' 监视变量 | ", style="magenta")
        footer_text.append("'q' 退出", style="green")
        return Panel(footer_text, height=4)
        
    def update_display(self):
        """更新显示"""
        if not self.layout:
            self.layout = self.create_layout()
            
        with self._lock:
            self.layout["header"].update(self.render_header())
            self.layout["variables"].update(self.render_variables())
            self.layout["watched"].update(self.render_watched())
            self.layout["call_stack"].update(self.render_call_stack())
            self.layout["execution"].update(self.render_execution_log())
            self.layout["current"].update(self.render_current())
            self.layout["breakpoints"].update(self.render_breakpoints())
            self.layout["footer"].update(self.render_footer())
        
    def start(self):
        """启动调试界面"""
        self.layout = self.create_layout()
        self.live = Live(self.layout, refresh_per_second=4, screen=True)
        self.live.start()
        
    def stop(self):
        """停止调试界面"""
        if self.live:
            self.live.stop()
            
    def trace_function(self, func):
        """装饰器：跟踪函数调用"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 获取调用信息
            frame = inspect.currentframe().f_back
            file_name = frame.f_code.co_filename
            line_no = frame.f_lineno
            
            func_name = f"{func.__module__}.{func.__name__}"
            args_dict = {f"arg{i}": str(arg)[:50] for i, arg in enumerate(args)}
            kwargs_dict = {k: str(v)[:50] for k, v in kwargs.items()}
            
            # 记录函数调用
            self.push_call(func_name, args_dict, kwargs_dict, file_name, line_no)
            self.update_display()
            
            # 检查是否需要暂停
            while self.paused:
                time.sleep(0.05)  # 更短的睡眠时间，提高响应性
                self.update_display()
                # 检查是否进入单步模式
                if self.step_mode:
                    with self._lock:
                        self.paused = True
                        self.step_mode = False
                    break
                # 检查是否恢复执行
                if not self.paused:
                    break
            
            try:
                # 执行函数
                result = func(*args, **kwargs)
                
                # 记录返回值
                if result is not None:
                    self.update_variable(f"{func.__name__}_result", result, func_name)
                
                self.pop_call(func_name, result)
                self.update_display()
                
                return result
            except Exception as e:
                self._log(f"❌ 错误: {func_name} - {str(e)}")
                self.pop_call(func_name)
                self.update_display()
                raise
                
        return wrapper

# 全局调试实例
workspace = DebugWorkspace()

