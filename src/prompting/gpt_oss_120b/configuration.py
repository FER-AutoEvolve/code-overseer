from dataclasses import dataclass
import dataclasses

from core import Result


@dataclass(frozen=True)
class GptOss120bConfiguration:
    '''
    Configuration for the GPT OSS 120B model.
    '''
    url: str
    api_key: str
    model: str = dataclasses.field(default="openai/gpt-oss-120b", init=False)
    max_tokens: int = 2000
    temperature: float|None = 0.2
    top_p: float|None = 1.0
    timeout: int = 60  # Timeout in seconds for API requests

    @staticmethod
    def from_dict(config: dict) -> Result['GptOss120bConfiguration']:
        '''
        Create an GptOss120bConfiguration from a dictionary of settings.
        Parameters:
            settings (dict): Dictionary containing 'ApiKey' and 'Model' keys.
        Returns:
            Result[GptOss120bConfiguration]: Result object containing GptOss120bConfiguration or error message.
        '''
        try:
            return Result.ok(GptOss120bConfiguration(
                url=config.get("Url", ""),
                api_key=config.get("ApiKey", ""),
                max_tokens=config.get("MaxTokens", 2000),
                temperature=config.get("Temperature", None),
                top_p=config.get("TopP", None),
                timeout=config.get("Timeout", 60)
            ))
        except ValueError as e:
            return Result.err(f"Invalid Local OSS settings: {e}")