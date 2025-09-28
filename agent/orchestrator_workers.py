from typing import Dict, List, Optional
from util import llm_call, extract_xml

def parse_tasks(tasks_xml: str) -> List[Dict]:
    """将 XML 任务解析为任务字典列表。"""
    tasks = []
    current_task = {}
    
    for line in tasks_xml.split('\n'):
        line = line.strip()
        if not line:
            continue
            
        if line.startswith("<task>"):
            current_task = {}
        elif line.startswith("<type>"):
            current_task["type"] = line[6:-7].strip()
        elif line.startswith("<description>"):
            current_task["description"] = line[12:-13].strip()
        elif line.startswith("</task>"):
            if "description" in current_task:
                if "type" not in current_task:
                    current_task["type"] = "default"
                tasks.append(current_task)
    
    return tasks

class FlexibleOrchestrator:
    """分解任务并使用worker并行运行LLMs."""
    
    def __init__(
        self,
        orchestrator_prompt: str,
        worker_prompt: str,
    ):
        """Initialize with prompt templates."""
        self.orchestrator_prompt = orchestrator_prompt
        self.worker_prompt = worker_prompt

    def _format_prompt(self, template: str, **kwargs) -> str:
        """Format a prompt template with variables."""
        try:
            return template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing required prompt variable: {e}")

    def process(self, task: str, context: Optional[Dict] = None) -> Dict:
        """Process task by breaking it down and running subtasks in parallel."""
        context = context or {}
        
        # Step 1: Get orchestrator response
        orchestrator_input = self._format_prompt(
            self.orchestrator_prompt,
            task=task,
            **context
        )
        orchestrator_response = llm_call(orchestrator_input)
        
        # Parse orchestrator response
        analysis = extract_xml(orchestrator_response, "analysis")
        tasks_xml = extract_xml(orchestrator_response, "tasks")
        tasks = parse_tasks(tasks_xml)
        
        print("\n=== ORCHESTRATOR OUTPUT ===")
        print(f"\nANALYSIS:\n{analysis}")
        print(f"\nTASKS:\n{tasks}")
        
        # Step 2: Process each task
        worker_results = []
        for task_info in tasks:
            worker_input = self._format_prompt(
                self.worker_prompt,
                original_task=task,
                task_type=task_info['type'],
                task_description=task_info['description'],
                **context
            )
            
            worker_response = llm_call(worker_input)
            result = extract_xml(worker_response, "response")
            
            worker_results.append({
                "type": task_info["type"],
                "description": task_info["description"],
                "result": result
            })
            
            print(f"\n=== WORKER RESULT ({task_info['type']}) ===\n{result}\n")
        
        return {
            "analysis": analysis,
            "worker_results": worker_results,
        }

ORCHESTRATOR_PROMPT = """
Analyze this task and break it down into 2-3 distinct approaches:

Task: {task}

Return your response in this format:

<analysis>
Explain your understanding of the task and which variations would be valuable.
Focus on how each approach serves different aspects of the task.
</analysis>

<tasks>
    <task>
    <type>formal</type>
    <description>Write a precise, technical version that emphasizes specifications</description>
    </task>
    <task>
    <type>conversational</type>
    <description>Write an engaging, friendly version that connects with readers</description>
    </task>
</tasks>
"""

WORKER_PROMPT = """
Generate content based on:
Task: {original_task}
Style: {task_type}
Guidelines: {task_description}

Return your response in this format:

<response>
Your content here, maintaining the specified style and fully addressing requirements.
</response>
"""


orchestrator = FlexibleOrchestrator(
    orchestrator_prompt=ORCHESTRATOR_PROMPT,
    worker_prompt=WORKER_PROMPT,
)

results = orchestrator.process(
    task="Write a product description for a new eco-friendly water bottle",
    context={
        "target_audience": "environmentally conscious millennials",
        "key_features": ["plastic-free", "insulated", "lifetime warranty"]
    }
)