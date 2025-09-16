from dataclasses import dataclass

from core import Result


@dataclass(frozen=True)
class OpenAiConfiguration:
    api_key: str
    model: str

    @staticmethod
    def from_dict(settings: dict) -> Result['OpenAiConfiguration']:
        try:
            return Result.ok(OpenAiConfiguration(
                api_key=settings.get("ApiKey", ""),
                model=settings.get("Model", "gpt-4")
            ))
        except ValueError as e:
            return Result.err(f"Invalid OpenAI settings: {e}")