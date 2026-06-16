from dataclasses import dataclass
import dataclasses

from core import Result


@dataclass(frozen=True)
class Gemma431bQatConfiguration:
    '''
    Configuration for the Gemma 4 31B QAT model.
    '''
    url: str
    api_key: str
    model: str = dataclasses.field(default="google/gemma-4-31b-qat", init=False)
    max_tokens: int = 2000
    temperature: float|None = 0.2
    top_p: float|None = 1.0
    timeout: int = 60
    headers: dict|None = dataclasses.field(default=None)

    @staticmethod
    def from_dict(config: dict) -> Result['Gemma431bQatConfiguration']:
        try:
            return Result.ok(Gemma431bQatConfiguration(
                url=config.get("Url", ""),
                api_key=config.get("ApiKey", ""),
                max_tokens=config.get("MaxTokens", 2000),
                temperature=config.get("Temperature", None),
                top_p=config.get("TopP", None),
                timeout=config.get("Timeout", 60),
                headers=config.get("Headers", None)
            ))
        except ValueError as e:
            return Result.err(f"Invalid Gemma 4 31B QAT settings: {e}")