import dataclasses

from core import Result

__DEFAULT_TIMEOUT__ = 10_000
__DEFAULT_MAX_BUILD_ATTEMPTS__ = 5

@dataclasses.dataclass(frozen=True)
class CodeBuildTestingConfiguration:
    is_enabled: bool
    code_build_tester_endpoint: str
    timeout: int = dataclasses.field(default=__DEFAULT_TIMEOUT__)
    max_build_attempts: int = dataclasses.field(default=__DEFAULT_MAX_BUILD_ATTEMPTS__)

    def from_dict(config: dict) -> Result['CodeBuildTestingConfiguration']:
        try:
            max_build_attempts = int(config.get("MaxBuildAttempts", __DEFAULT_MAX_BUILD_ATTEMPTS__))
            if max_build_attempts < 1:
                return Result.err("CodeBuildTesting.MaxBuildAttempts must be at least 1")

            return Result.ok(CodeBuildTestingConfiguration(
                is_enabled=config.get("Enabled"),
                code_build_tester_endpoint=config.get("Endpoint"),
                timeout=int(config.get("Timeout", __DEFAULT_TIMEOUT__)),
                max_build_attempts=max_build_attempts
            ))
        except Exception as e:
            return Result.err(f"{e}")