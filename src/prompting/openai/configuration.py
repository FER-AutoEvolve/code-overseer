from dataclasses import dataclass

from core import Result


@dataclass(frozen=True)
class OpenAiConfiguration:
    '''Configuration for the generic OpenAI API provider.'''
    api_key: str
    model: str
    max_tokens: int = 200
    temperature: float | None = 0.2
    top_p: float | None = 1.0
    timeout: int = 60

    @staticmethod
    def from_dict(config: dict) -> Result['OpenAiConfiguration']:
        model = str(config.get("Model", "")).strip()
        if not model:
            return Result.err("OpenAI configuration requires 'Model' to be set.")

        try:
            return Result.ok(OpenAiConfiguration(
                api_key=config.get("ApiKey", ""),
                model=model,
                max_tokens=config.get("MaxTokens", 200),
                temperature=config.get("Temperature", None),
                top_p=config.get("TopP", None),
                timeout=config.get("Timeout", 60)
            ))
        except ValueError as error:
            return Result.err(f"Invalid OpenAI settings: {error}")