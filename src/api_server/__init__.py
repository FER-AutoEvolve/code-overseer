import dataclasses
from typing import Any
from fastapi import FastAPI
from code_overseeing import CodeOverseer
from configuration import FastApiConfiguration
from core import Result, Unit
import uvicorn
import logging

from api_server.dtos import CodeChangeRequest

@dataclasses.dataclass(frozen=False)
class ApiServer:
    _apiConfiguration: FastApiConfiguration
    _code_overseer: CodeOverseer
    _server: Any
    _logger: logging.Logger = dataclasses.field(default=logging.getLogger(__name__))
    _app: FastAPI = dataclasses.field(default_factory=lambda: FastAPI(), init=False)

    def start_server(self) -> Result[Unit]:
        '''Starts the FastAPI server'''
        try:
            self._define_endpoints()
            self._server = uvicorn.run(self._app, host=self._apiConfiguration.host, port=self._apiConfiguration.port, log_config=None, log_level=self._logger.level)
            return Result.ok(Unit())
        except Exception as e:
            return Result.err(str(e))

    def stop_server(self) -> Result[Unit]:
        '''Stops the FastAPI server'''
        try:
            # stop the server
            self._server.stop()
            return Result.ok(Unit())
        except Exception as e:
            return Result.err(str(e))

    def _define_endpoints(self) -> None:
        '''Defines the FastAPI endpoints'''
    
        @self._app.get("/health")
        async def _health():
            '''Responds if the server is running'''
            return {"status": "healthy"}
        
        from fastapi import Body

        @self._app.post("/code_change")
        async def _code_change(request: CodeChangeRequest = Body(...)):
            '''Handles code change requests'''
            self._logger.info(f"Received code change request: {request.change_strategic_description}")
            res_code_change = self._code_overseer.apply_code_change(request.change_strategic_description)
            if res_code_change.is_err():
                self._logger.error(f"Failed to apply code change: {res_code_change.unwrap_err()}")
                return {"status": "error", "message": res_code_change.unwrap_err()}
            return {"status": "Applied code change successfully"}
