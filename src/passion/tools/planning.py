from agentscope.tool import ToolResponse

class PlanManager:
    def __init__(self):
        self.tasks = []

    def create_plan(self, tasks: list[str]) -> str:
        self.tasks = [{"description": t, "status": "pending"} for t in tasks]
        return self._render_plan()

    def mark_task_completed(self, task_index: int, result: str = "") -> str:
        if 0 <= task_index < len(self.tasks):
            self.tasks[task_index]["status"] = "completed"
            self.tasks[task_index]["result"] = result
            return f"Task {task_index+1} marked as completed.\n" + self._render_plan()
        return f"Error: Invalid task index {task_index+1}."

    def add_task(self, description: str) -> str:
        self.tasks.append({"description": description, "status": "pending"})
        return f"Task added.\n" + self._render_plan()

    def get_plan(self) -> str:
        if not self.tasks:
            return "No plan active."
        return self._render_plan()

    def _render_plan(self) -> str:
        output = ["Current Plan:"]
        for i, task in enumerate(self.tasks):
            status_icon = "✅" if task["status"] == "completed" else "⬜"
            output.append(f"{i+1}. {status_icon} {task['description']}")
            if task.get("result"):
                output.append(f"   Result: {task['result']}")
        return "\n".join(output)

_PLAN_MANAGER = PlanManager()

def create_plan(tasks: list[str]) -> ToolResponse:
    """
    Create a new plan with a list of tasks to accomplish a goal.
    
    Args:
        tasks (list[str]): A list of task descriptions.
    """
    result = _PLAN_MANAGER.create_plan(tasks)
    return ToolResponse(content=result)

def mark_task_completed(task_index: int, result: str = "") -> ToolResponse:
    """
    Mark a specific task in the plan as completed.
    
    Args:
        task_index (int): The 1-based index of the task to mark as completed.
        result (str): Optional summary of the result of the task.
    """
    # Adjust for 0-based index internally
    res = _PLAN_MANAGER.mark_task_completed(task_index - 1, result)
    return ToolResponse(content=res)

def get_plan() -> ToolResponse:
    """
    Retrieve the current status of the plan.
    """
    return ToolResponse(content=_PLAN_MANAGER.get_plan())

def add_task(description: str) -> ToolResponse:
    """
    Add a new task to the end of the current plan.
    
    Args:
        description (str): Description of the new task.
    """
    res = _PLAN_MANAGER.add_task(description)
    return ToolResponse(content=res)
