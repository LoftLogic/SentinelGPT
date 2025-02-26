from typing import Optional

import threading
import json
import socket
import logging
import base64

from .sandbox import PlanExecutionSandbox, ToolExecutionSandbox
from ..schema.tool import Tool
from ..schema.plan import Plan

logger = logging.getLogger(__name__)


class PlanOrchestrator:
    plan: Plan
    tools: dict[str, Tool]
    plan_execution_sandbox: Optional[PlanExecutionSandbox]
    tool_execution_sandbox: Optional[ToolExecutionSandbox]
    listener_thread: Optional[threading.Thread]
    shutdown: threading.Event

    def __init__(self, plan: Plan, tools: dict[str, Tool]):
        self.plan = plan
        self.tools = tools
        self.shutdown = threading.Event()

    def launch(self) -> None:
        # Start listener thread
        self.listener_thread = threading.Thread(
            target=self.__start_listener,
            args=("0.0.0.0", 65432),
            daemon=True
        )
        self.listener_thread.start()

        # Launch plan execution container and wait for port to open
        self.plan_execution_sandbox = PlanExecutionSandbox(self.plan)
        self.plan_execution_sandbox.launch()
        self.plan_execution_sandbox.wait_for_port()

        # TODO: Verify that the container is running

    def join(self) -> None:
        self.listener_thread.join()

    def handle_invoke(self, tool_name: str, tool_args: list, tool_kwargs: dict) -> None:
        # Execute tool and retrieve result
        tool = self.tools[tool_name]
        self.tool_execution_sandbox = ToolExecutionSandbox(tool)
        self.tool_execution_sandbox.launch(tool_args, tool_kwargs)
        self.tool_execution_sandbox.wait_for_result()
        result = self.tool_execution_sandbox.result

        # Encode result
        result_b64 = base64.b64encode(json.dumps(result).encode()).decode()

        # Send result back to worker
        self.plan_execution_sandbox.send(f"RESPONSE: {result_b64}")

    def handle_print(self, message: str) -> None:
        print(message)

    # def handle_info(self, message: str) -> None:
    #     raise NotImplementedError

    def handle_terminate(self) -> None:
        self.plan_execution_sandbox.kill()
        self.shutdown.set()

    def __handle_client(self, client_socket: socket.socket, addr: tuple[str, int]) -> None:
        logger.info(f"New connection from {addr}")

        try:
            while True:
                message = client_socket.recv(1024).decode()
                if not message:
                    break

                if message.startswith("INVOKE:"):
                    msg_b64 = message[len("INVOKE:"):]
                    msg_json = base64.b64decode(msg_b64).decode()
                    tool_name, tool_args, tool_kwargs = json.loads(msg_json)
                    self.handle_invoke(tool_name, tool_args, tool_kwargs)
                elif message.startswith("PRINT:"):
                    msg_b64 = message[len("PRINT:"):]
                    msg_str = base64.b64decode(msg_b64).decode()
                    self.handle_print(msg_str)
                # elif message.startswith("INFO:"):
                #     self.handle_info(message[len("INFO:"):])
                elif message == "TERMINATE":
                    self.handle_terminate()
                    break
                else:
                    logger.warning(f"Unknown message from {addr}: {message}")
        except ConnectionResetError:
            logger.warning(f"Connection lost with {addr}")
        finally:
            client_socket.close()

    def __start_listener(self, ip: str, port: int, backlog: int = 5) -> None:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.settimeout(1.0)
        server.bind((ip, port))
        server.listen(backlog)
        logger.info(f"Listener thread listening on {ip}:{port}")

        # while True:
        while not self.shutdown.is_set():
            try:
                client_socket, addr = server.accept()
            except socket.timeout:
                continue
            threading.Thread(
                target=self.__handle_client,
                args=(client_socket, addr),
                daemon=True
            ).start()
