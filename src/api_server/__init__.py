import dataclasses
from typing import Any
from fastapi import FastAPI, HTTPException
from code_overseeing import CodeOverseer
from configuration import FastApiConfiguration
from core import Result, Unit
import uvicorn
import logging
import threading

from api_server.dtos import CodeChangeRequest

@dataclasses.dataclass(frozen=False)
class ApiServer:
    _is_task_running: bool = dataclasses.field(default=False, init=False)
    _apiConfiguration: FastApiConfiguration
    _code_overseer: CodeOverseer
    _server: uvicorn.Server | None = dataclasses.field(default=None, init=False)
    _logger: logging.Logger = dataclasses.field(default=logging.getLogger())
    _app: FastAPI = dataclasses.field(default_factory=lambda: FastAPI(), init=False)
    _server_thread: threading.Thread | None = dataclasses.field(default=None, init=False)

    def start_server(self) -> Result[Unit]:
        '''
        Starts the FastAPI server in separate thread.
        Returns:
            Result[Unit]: Result indicating success or failure.
        '''
        try:
            self._define_endpoints()
            server_config = uvicorn.Config(app=self._app, host=self._apiConfiguration.host, port=self._apiConfiguration.port, log_level=self._logger.level)
            self._server = uvicorn.Server(config=server_config)
            self._server_thread = threading.Thread(target=self._server.run, daemon=True)
            self._server_thread.start()
            return Result.ok(Unit())
        except Exception as e:
            return Result.err(str(e))
        
    def wait_for_server_to_stop(self) -> Result[Unit]:
        '''
        Waits for the FastAPI server to stop.
        Returns:
            Result[Unit]: Result indicating success or failure.
        '''
        try:
            if self._server_thread and self._server_thread.is_alive():
                self._server_thread.join()
            return Result.ok(Unit())
        except Exception as e:
            return Result.err(str(e))

    def stop_server(self) -> Result[Unit]:
        '''
        Stops the FastAPI server
        Returns:
            Result[Unit]: Result indicating success or failure.
        '''
        try:
            # stop the server
            if self._server:
                self._server.should_exit = True
            if self._server_thread:
                self._server_thread.join()
            return Result.ok(Unit())
        except Exception as e:
            return Result.err(str(e))

    def _define_endpoints(self) -> None:
        '''
        Defines the FastAPI endpoints
        '''
    
        @self._app.get("/health")
        async def _health():
            '''Responds if the server is running'''
            return {"status": "healthy"}
        
        from fastapi import Body

        import threading

        @self._app.post("/code-change")
        async def _code_change(request: CodeChangeRequest = Body(...)):
            '''Handles code change requests
             Args:
                 request (CodeChangeRequest): The code change request.
             Returns:
                 dict: A dictionary indicating success or failure.
            '''
            self._logger.info(f"Received code change request: {request.change_strategic_description}")

            if self._is_task_running:
                raise HTTPException(status_code=429, detail="A code change task is already running. Please wait until it completes.")

            self._is_task_running = True

            def apply_code_change_in_background():
                try:
                    res_code_change = self._code_overseer.apply_code_change(request.change_strategic_description)
                    if res_code_change.is_err():
                        self._logger.error(f"Failed to apply code change: {res_code_change.message}")
                finally:
                    self._is_task_running = False

            threading.Thread(target=apply_code_change_in_background, daemon=True).start()
            return {"status": "Code change job started"}
