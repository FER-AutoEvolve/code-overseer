from dataclasses import dataclass
import dataclasses

from core import Result


@dataclass(frozen=True)
class Nemotron3SuperConfiguration:
    '''
    Configuration for the Nemotron 3 Super model.
    '''
    url: str
    api_key: str
    model: str = dataclasses.field(default="nvidia/nemotron-3-super", init=False)
    max_tokens: int = 2000
    temperature: float|None = 0.2
    top_p: float|None = 1.0
    timeout: int = 60
    headers: dict|None = dataclasses.field(default=None)

    @staticmethod
    def from_dict(config: dict) -> Result['Nemotron3SuperConfiguration']:
        try:
            return Result.ok(Nemotron3SuperConfiguration(
                url=config.get("Url", ""),
                api_key=config.get("ApiKey", ""),
                max_tokens=config.get("MaxTokens", 2000),
                temperature=config.get("Temperature", None),
                top_p=config.get("TopP", None),
                timeout=config.get("Timeout", 60),
                headers=config.get("Headers", None)
            ))
        except ValueError as e:
            return Result.err(f"Invalid Nemotron 3 Super settings: {e}")