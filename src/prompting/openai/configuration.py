from dataclasses import dataclass

from configuration import Configuration, PromptingProviders
from core import Result


@dataclass(frozen=True)
class OpenAiConfiguration:
    '''
    Configuration for OpenAI API.
    '''
    api_key: str
    model: str
    max_tokens: int = 200
    temperature: float = 0.2
    top_p: float = 1.0
    timeout: int = 60  # Timeout in seconds for API requests

    @staticmethod
    def from_dict(config: dict) -> Result['OpenAiConfiguration']:
        '''
        Create an OpenAiConfiguration from a dictionary of settings.
        Parameters:
            settings (dict): Dictionary containing 'ApiKey' and 'Model' keys.
        Returns:
            Result[OpenAiConfiguration]: Result object containing OpenAiConfiguration or error message.
        '''
        try:
            return Result.ok(OpenAiConfiguration(
                api_key=config.get("ApiKey", ""),
                model=config.get("Model", "gpt-4o"),
                max_tokens=config.get("MaxTokens", 200),
                temperature=config.get("Temperature", 0.2),
                top_p=config.get("TopP", 1.0),
                timeout=config.get("Timeout", 60)
            ))
        except ValueError as e:
            return Result.err(f"Invalid OpenAI settings: {e}")