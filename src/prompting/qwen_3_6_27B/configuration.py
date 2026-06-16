from dataclasses import dataclass
import dataclasses

from core import Result


@dataclass(frozen=True)
class Qwen3627bConfiguration:
    '''
    Configuration for the Qwen 3.6 27B model.
    '''
    url: str
    api_key: str
    model: str = dataclasses.field(default="qwen/qwen3.6-27b", init=False)
    max_tokens: int = 2000
    temperature: float|None = 0.2
    top_p: float|None = 1.0
    timeout: int = 60
    headers: dict|None = dataclasses.field(default=None)

    @staticmethod
    def from_dict(config: dict) -> Result['Qwen3627bConfiguration']:
        try:
            return Result.ok(Qwen3627bConfiguration(
                url=config.get("Url", ""),
                api_key=config.get("ApiKey", ""),
                max_tokens=config.get("MaxTokens", 2000),
                temperature=config.get("Temperature", None),
                top_p=config.get("TopP", None),
                timeout=config.get("Timeout", 60),
                headers=config.get("Headers", None)
            ))
        except ValueError as e:
            return Result.err(f"Invalid Qwen 3.6 27B settings: {e}")