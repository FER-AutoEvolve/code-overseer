from dataclasses import dataclass
from typing import Any
from fastapi import FastAPI
from code_overseeing import CodeOverseer
from configuration import FastApiConfiguration
from core import Result, Unit
import uvicorn
import logging

@dataclass(frozen=False)
class ApiServer:
    _app: FastAPI
    _code_overseer: CodeOverseer
    _apiConfiguration: FastApiConfiguration
    _server: Any
    _logger: logging.Logger

    def __init__(self, api_config: FastApiConfiguration, code_overseer: CodeOverseer, logger: logging.Logger = logging.getLogger(__name__)) -> None:
        self._apiConfiguration = api_config
        self._code_overseer = code_overseer
        self._logger = logger
        self._app = FastAPI()
        self._server = None

    def start_server(self) -> Result[Unit]:
        '''Starts the FastAPI server'''
        try:
            # create the FastAPI app and define the endpoints; start the server
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
            self._code_overseer.handle_code_change(request.change_strategic_description)
            return {"status": "code change received"}


@dataclass(frozen=True)
class CodeChangeRequest:
    change_strategic_description: str