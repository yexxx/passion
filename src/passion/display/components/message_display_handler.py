"""
Message Display Handler - Final Perfected Version + Real-time Thinking
Features:
- Real-time Thinking: Shows the specific thought process in the spinner.
- Fixed Duplicate Logs: Ensures 'Using tool' only prints when block_id is stable.
- Improved Indentation: Hierarchy for Plan Title vs Tasks.
- "Tail-f" Streaming & Auto-scrolling.
- Robust Input merging.
"""
import sys
from typing import Dict, Any, Optional, Set
from agentscope.message import Msg
from rich.console import Console, Group
from rich.live import Live
from rich.spinner import Spinner
from rich.text import Text
from rich.panel import Panel
from rich.syntax import Syntax
from rich.rule import Rule
from rich.table import Table
from rich import box 

class MessageDisplayHandler:
    def __init__(self, display_manager: Any = None, name: str = "Passion"):
        self.display_manager = display_manager 
        self.name = name
        self.console = Console()
        
        self.PLAN_TOOLS = ["create_plan", "mark_task_completed", "add_task", "get_plan"]
        
        # Live 实例池
        self.status_live: Optional[Live] = None
        self.active_tool_lives: Dict[str, Live] = {}
        
        # 状态追踪
        self._printed_keys: Set[str] = set()
        self._has_responded = False
        self._finished_msg_ids: Set[str] = set()
        self._stream_lengths: Dict[str, int] = {}
        self._tool_inputs: Dict[str, dict] = {}
        
        # 记录所有已经停止/结束的 block_id，防止跨回合重复渲染
        self._stopped_block_ids: Set[str] = set()

    def _update_status_spinner(self, text: str):
        """更新或启动底部的状态 Spinner"""
        if self._has_responded: return
        
        # 使用 dim 样式让思考过程看起来不那么刺眼
        spinner = Spinner("dots", text=Text(f" {text}", style="cyan"))
        
        if self.status_live is None:
            self.status_live = Live(spinner, console=self.console, refresh_per_second=12, transient=True)
            self.status_live.start()
        else:
            self.status_live.update(spinner)

    def _stop_status_spinner(self):
        if self.status_live is not None:
            try: self.status_live.stop()
            except: pass
            finally: self.status_live = None

    def _get_tracker_key(self, msg_id: str, block_id: Optional[str], suffix: str = "") -> str:
        if block_id:
            return f"tool:{block_id}:{suffix}"
        else:
            return f"msg:{msg_id}:{suffix}"

    def handle_thinking_display(self, msg: Msg) -> bool:
        """
        处理思考过程显示。
        [新增功能] 实时提取思考内容的最后一行显示在 Spinner 上。
        """
        if msg.id in self._finished_msg_ids: return False
        content = msg.content if isinstance(msg.content, list) else [{"type": "text", "text": str(msg.content)}]
        
        for block in content:
            if block.get("type") == "thinking":
                if not self._has_responded:
                    # 获取思考的完整文本
                    thought_content = block.get("thinking", "")
                    
                    display_text = "Passion is thinking..."
                    
                    # 提取最后一行非空文本，让用户看到它正在想什么
                    if thought_content:
                        # 按行分割，过滤空行
                        lines = [line.strip() for line in thought_content.split('\n') if line.strip()]
                        if lines:
                            last_line = lines[-1]
                            # 如果太长，截取后60个字符，保留句尾信息
                            if len(last_line) > 60:
                                last_line = "..." + last_line[-57:]
                            
                            # 移除 markdown 标记防止格式混乱
                            last_line = last_line.replace("```", "").replace("#", "")
                            display_text = f"Thinking: {last_line}"

                    self._update_status_spinner(display_text)
                return True
        return False

    def handle_tool_use_display(self, msg: Msg, last: bool = True) -> bool:
        if msg.id in self._finished_msg_ids: return False

        content = msg.content if isinstance(msg.content, list) else [{"type": "text", "text": str(msg.content)}]
        msg_id = msg.id
        processed_any = False

        for block in content:
            block_type = block.get("type")
            block_id = block.get("id")
            
            if block_type == "tool_use":
                if not block_id: continue
                
                tool_name = block.get("name")
                tool_input = block.get("input", {})
                
                # 1. 参数持久化
                if block_id not in self._tool_inputs:
                    self._tool_inputs[block_id] = {}
                if isinstance(tool_input, dict) and tool_input:
                    self._tool_inputs[block_id].update(tool_input)
                
                start_key = self._get_tracker_key(msg_id, block_id, "tool_start")
                
                # 2. 显示“工具开始”
                if start_key not in self._printed_keys:
                    self.console.print(f"[dim]🛠️  Using tool: {tool_name}...[/dim]")
                    self._printed_keys.add(start_key)

                is_streaming_tool = tool_name in ["execute_python_code", "execute_shell_command", "write_text_file"]
                
                if is_streaming_tool:
                    self._stop_status_spinner()
                    full_input = self._tool_inputs[block_id]
                    self._handle_streaming_panel(block_id, tool_name, full_input)
                else:
                    action_text = f"Updating plan..." if tool_name in self.PLAN_TOOLS else f"Running {tool_name}..."
                    self._update_status_spinner(action_text)

                processed_any = True
        return processed_any

    def _handle_streaming_panel(self, block_id, tool_name, tool_input):
        if block_id in self._stopped_block_ids:
            return

        tool_config = {
            "execute_python_code": ("code", "Python Code", "python", "code"),
            "execute_shell_command": ("command", "Shell Command", "bash", "command"),
            "write_text_file": ("content", "Writing File", "markdown", "file_path")
        }
        
        if tool_name not in tool_config: return
        key, title_prefix, lexer, meta_key = tool_config[tool_name]
        
        if meta_key not in tool_input and key not in tool_input: return
        content_str = tool_input.get(key, "")
        if not content_str and block_id not in self.active_tool_lives: return

        if tool_name == "write_text_file":
            file_path = tool_input.get("file_path", "Unknown File")
            title = f"{title_prefix}: {file_path}"
        else:
            title = title_prefix

        if block_id not in self.active_tool_lives:
            if self._has_responded: self.console.print()
            
            renderable = self._create_panel_renderable(content_str, title, lexer)
            live = Live(renderable, console=self.console, refresh_per_second=10)
            live.start()
            self.active_tool_lives[block_id] = live
        else:
            live = self.active_tool_lives[block_id]
            renderable = self._create_panel_renderable(content_str, title, lexer)
            live.update(renderable)

    def _create_panel_renderable(self, content: str, title: str, lexer: str):
        if not content: content = " "
        
        if lexer in ["python", "bash"]:
            MAX_LINES = 8
        else:
            MAX_LINES = 3 

        lines = content.splitlines()
        total_lines = len(lines)
        
        render_objects = []
        
        if total_lines > MAX_LINES:
            hidden_count = total_lines - MAX_LINES
            visible_lines = lines[-MAX_LINES:]
            
            info_text = Text(f"... ({hidden_count} lines hidden)", style="dim italic")
            render_objects.append(info_text)
            
            display_content = "\n".join(visible_lines)
            start_line_number = hidden_count + 1 
        else:
            display_content = content
            start_line_number = 1
            
        if lexer == "python" or lexer == "bash":
            code_block = Syntax(
                display_content, 
                lexer, 
                theme="monokai", 
                line_numbers=True, 
                start_line=start_line_number, 
                word_wrap=True
            )
            render_objects.append(code_block)
        else:
            render_objects.append(Text(display_content))

        return Panel(
            Group(*render_objects), 
            title=f"[bold]{title}[/]", 
            border_style="blue", 
            padding=(0, 1)
        )

    def handle_tool_result_display(self, msg: Msg) -> bool:
        if msg.id in self._finished_msg_ids: return False
        
        content = msg.content if isinstance(msg.content, list) else [{"type": "text", "text": str(msg.content)}]
        msg_id = msg.id
        processed_any = False

        for block in content:
            if block.get("type") == "tool_result":
                block_id = block.get("id")
                end_key = self._get_tracker_key(msg_id, block_id, "tool_end")

                if end_key not in self._printed_keys:
                    if block_id in self.active_tool_lives:
                        self.active_tool_lives[block_id].stop()
                        del self.active_tool_lives[block_id]
                    self._stopped_block_ids.add(block_id)
                    
                    self._stop_status_spinner()

                    tool_name = block.get("name", "Tool")
                    raw_output = block.get("output")

                    if raw_output is None or str(raw_output).strip() == "" or str(raw_output) == "None":
                        self._printed_keys.add(end_key)
                        continue 

                    # Plan 清单
                    if tool_name in self.PLAN_TOOLS:
                        lines = str(raw_output).strip().split('\n')
                        self.console.print() 
                        self.console.print("  [bold]📋 Current Plan[/]") 
                        
                        for line in lines:
                            line = line.strip()
                            if not line or "Current Plan:" in line or "marked as completed" in line or line.startswith("Result:"): 
                                continue
                            if line[0].isdigit() and ". " in line:
                                try:
                                    parts = line.split(". ", 1)
                                    rest = parts[1]
                                    if " " in rest:
                                        icon, desc = rest.split(" ", 1)
                                    else:
                                        icon, desc = rest, ""
                                    
                                    if "✅" in icon:
                                        self.console.print(f"    [green]{icon}[/] {desc}")
                                    else:
                                        self.console.print(f"    [dim]{icon} {desc}[/dim]")
                                except:
                                    self.console.print(f"    {line}")
                        self.console.print() 
                    
                    else:
                        tool_input = self._tool_inputs.get(block_id, {})
                        
                        file_path = tool_input.get("file_path") or tool_input.get("filename") or tool_input.get("path") or "unknown file"
                        
                        summary = ""
                        if tool_name == "view_text_file":
                            summary = f"read: {file_path}"
                        elif tool_name == "write_text_file":
                            summary = f"wrote to: {file_path}"
                        else:
                            output_str = str(raw_output).strip()
                            output_single_line = output_str.replace("\n", " ").replace("\r", "")
                            if len(output_single_line) > 50:
                                summary = output_single_line[:50] + "..."
                            else:
                                summary = output_single_line

                        self.console.print(f"[bold green]✓[/] {tool_name} executed. [dim]({summary})[/]")
                    
                    self._printed_keys.add(end_key)
                    
                    if not self._has_responded:
                        self._update_status_spinner("Passion is analyzing results...")
                
                processed_any = True
        return processed_any

    def handle_text_display(self, msg: Msg) -> bool:
        if msg.id in self._finished_msg_ids: return False

        content = msg.content if isinstance(msg.content, list) else [{"type": "text", "text": str(msg.content)}]
        msg_id = msg.id
        processed_any = False

        for block in content:
            if block.get("type") == "text":
                text = block.get("text", "")
                
                stream_key = self._get_tracker_key(msg_id, None, "text_len")
                prev_len = self._stream_lengths.get(stream_key, 0)

                if len(text) > prev_len:
                    self._stop_status_spinner()
                    self._has_responded = True

                    if prev_len == 0:
                        self.console.print(f"\n[bold blue]{self.name}:[/] ", end="")
                    
                    new_chunk = text[prev_len:]
                    self.console.print(new_chunk, end="", highlight=False)
                    
                    self._stream_lengths[stream_key] = len(text)
                
                processed_any = True
        return processed_any

    def handle_final_cleanup(self, msg: Msg, last: bool = True) -> None:
        if not last: return
        if msg.id in self._finished_msg_ids: return

        self._stop_status_spinner()
        
        # 清理时，将所有活跃的 block_id 加入黑名单
        for block_id, live in self.active_tool_lives.items():
            try: live.stop()
            except: pass
            self._stopped_block_ids.add(block_id)
            
        self.active_tool_lives.clear()
        
        self._finished_msg_ids.add(msg.id)
        
        stream_key = self._get_tracker_key(msg.id, None, "text_len")
        has_text = stream_key in self._stream_lengths
        
        if has_text:
            self.console.print() 
        
        self.console.print(Rule(style="dim"))
        self._has_responded = False