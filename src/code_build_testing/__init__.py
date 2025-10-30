import dataclasses
from typing import Any, Dict
import requests
from code_build_testing.configuration import CodeBuildTestingConfiguration
from core import Result, Unit


@dataclasses.dataclass(frozen=True)
class BuildResultDto:
    is_success: bool
    error_message: str|None = dataclasses.field(default=None)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "IsSuccess": self.is_success,
            "ErrorMessage": self.error_message
        }
    
    @staticmethod
    def from_dto(dto: dict) -> Result['BuildResultDto']:
        try:
            return Result.ok(BuildResultDto(
                is_success=dto.get("IsSuccess"),
                error_message=dto.get("ErrorMessage", None)
            ))
        except Exception as e:
            return Result.err(f"Failed to parse build result DTO: {e}")

@dataclasses.dataclass(frozen=True)
class CodeBuildTestProvider:
    _configuration: CodeBuildTestingConfiguration

    def try_build(self) -> Result[BuildResultDto]:
        try:
            response = requests.get(self._configuration.code_build_tester_endpoint, timeout=self._configuration.timeout)
            if response.status_code != 200:
                return Result.err(f"Code build tester returned non-200 status code: {response.status_code}")
            dto = response.json()
            res_build_result = BuildResultDto.from_dto(dto)
            if res_build_result.is_err():
                return Result.err(res_build_result.message)
            return Result.ok(res_build_result.value)
        except Exception as e:
            return Result.err(f"Failed to get code test build result: {e}")
