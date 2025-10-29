import dataclasses

from core import Result

__DEFAULT_TIMEOUT__ = 10_000

@dataclasses.dataclass(frozen=True)
class CodeBuildTestingConfiguration:
    is_enabled: bool
    code_build_tester_endpoint: str
    timeout: int = dataclasses.field(default=__DEFAULT_TIMEOUT__)

    def from_dict(config: dict) -> Result['CodeBuildTestingConfiguration']:
        try:
            return Result.ok(CodeBuildTestingConfiguration(
                is_enabled=config.get("IsEnabled"),
                code_build_tester_endpoint=config.get("CodeBuildTesterEndpoint"),
                timeout=config.get("Timeout", __DEFAULT_TIMEOUT__)
            ))
        except Exception as e:
            return Result.err(f"{e}")