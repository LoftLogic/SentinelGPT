from typing import Optional, Any
from enum import Enum

import docker
import docker.models
import docker.models.containers
import threading
import base64
import json
import logging

from ..schema.tool import Tool
from ..schema.plan import Plan
from .helper import write_to_socket

logger = logging.getLogger(__name__)


class ExecutionStatus(Enum):
    NOT_STARTED = 0
    PENDING = 1
    RUNNING = 2
    COMPLETED = 3
    FAILED = 4


class PlanExecutionSandbox:
    plan: Plan
    container: Optional[docker.models.containers.Container]

    def __init__(self, plan: Plan):
        self.plan = plan

    def launch(self) -> None:
        # Prepare container inputs
        plan_code = self.plan.script
        plan_code_b64 = base64.b64encode(plan_code.encode())
        docker_env = {"SCRIPT": plan_code_b64}

        # Spawn plan execution container
        docker_client = docker.from_env()
        container = docker_client.containers.run(
            image="worker-image",
            environment=docker_env,
            detach=True,
            ports={"8080/tcp": None},
        )

        self.container = container

    def wait_for_port(self) -> None:
        # TODO: make this more robust
        if not self.container:
            raise RuntimeError("Container not launched")

        while not self.container.ports:
            self.container.reload()
            if self.container.status == "exited":
                raise RuntimeError("Container exited unexpectedly")

    def send(self, message: str) -> None:
        if not self.container:
            raise RuntimeError("Container not launched")

        writer_thread = threading.Thread(
            target=write_to_socket,
            args=(self.addr, message)
        )
        writer_thread.start()

    def kill(self) -> None:
        # TODO: think about how to handle errors
        if not self.container:
            raise RuntimeError("Container not launched")
        try:
            self.container.kill()
        except Exception as e:
            pass

    @property
    def status(self) -> ExecutionStatus:
        if not self.container:
            return ExecutionStatus.NOT_STARTED
        elif self.container.status == "exited":
            return ExecutionStatus.COMPLETED
        elif self.container.status == "running":
            return ExecutionStatus.RUNNING
        else:
            return ExecutionStatus.FAILED

    @property
    def port(self) -> int:
        if not self.container.ports:
            raise RuntimeError("Container port not open")
        return int(self.container.ports["8080/tcp"][0]["HostPort"])

    @property
    def ip(self) -> str:
        return "127.0.0.1"
        # return self.container.attrs["NetworkSettings"]["IPAddress"]

    @property
    def addr(self) -> tuple[str, int]:
        return (self.ip, self.port)


class ToolExecutionSandbox:
    tool: Tool
    has_run: bool
    container: Optional[docker.models.containers.Container]

    def __init__(self, tool: Tool):
        self.tool = tool
        self.has_run = False

    def launch(
        self,
        args: list[Any] = [],
        kwargs: dict[str, Any] = {}
    ) -> None:
        # Enforce input typing
        # TODO: enforce input typing according to tool schema

        # Prepare container inputs
        src_code = self.tool.source_code
        kwargs_json = json.dumps(kwargs)
        args_json = json.dumps(args)
        src_code_b64 = base64.b64encode(src_code.encode())
        args_b64 = base64.b64encode(args_json.encode())
        kwargs_b64 = base64.b64encode(kwargs_json.encode())
        docker_env = {
            "TOOL_CODE": src_code_b64,
            "ARGS": args_b64,
            "KWARGS": kwargs_b64,
            "FUNC_NAME": self.tool.func_name
        }

        # Spawn tool environment
        docker_client = docker.from_env()
        self.container = docker_client.containers.run(
            image="tool-runner-image",
            environment=docker_env,
            detach=True,
            ports={"8080/tcp": None},
        )

    def wait_for_result(self, timeout: Optional[float] = None) -> None:
        if not self.container:
            raise RuntimeError("Container not launched")
        self.container.wait(timeout=timeout)

    def kill(self) -> None:
        if not self.container:
            raise RuntimeError("Container not launched")
        self.container.kill()

    @property
    def status(self) -> ExecutionStatus:
        if not self.container:
            return ExecutionStatus.NOT_STARTED
        elif self.container.status == "exited":
            return ExecutionStatus.COMPLETED
        elif self.container.status == "running":
            return ExecutionStatus.RUNNING
        else:
            return ExecutionStatus.FAILED

    @property
    def result(self) -> Any:
        # TODO: conform output to tool output schema
        if not self.container:
            raise RuntimeError("Container not launched")
        output_b64 = self.container.logs().decode()
        output = json.loads(base64.b64decode(output_b64).decode())
        return output
