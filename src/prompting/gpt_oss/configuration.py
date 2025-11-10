from dataclasses import dataclass

from core import Result


@dataclass(frozen=True)
class GptOssConfiguration:
    '''
    Configuration for OpenAI API.
    '''
    url: str
    api_key: str
    model: str
    max_tokens: int = 2000
    temperature: float|None = 0.2
    top_p: float|None = 1.0
    timeout: int = 60  # Timeout in seconds for API requests

    @staticmethod
    def from_dict(config: dict) -> Result['GptOssConfiguration']:
        '''
        Create an GptOssConfiguration from a dictionary of settings.
        Parameters:
            settings (dict): Dictionary containing 'ApiKey' and 'Model' keys.
        Returns:
            Result[GptOssConfiguration]: Result object containing GptOssConfiguration or error message.
        '''
        try:
            return Result.ok(GptOssConfiguration(
                url=config.get("Url", ""),
                api_key=config.get("ApiKey", ""),
                model=config.get("Model", ""),
                max_tokens=config.get("MaxTokens", 2000),
                temperature=config.get("Temperature", None),
                top_p=config.get("TopP", None),
                timeout=config.get("Timeout", 60)
            ))
        except ValueError as e:
            return Result.err(f"Invalid Local OSS settings: {e}")