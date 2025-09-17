from dataclasses import dataclass

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

    @staticmethod
    def from_dict(settings: dict) -> Result['OpenAiConfiguration']:
        '''
        Create an OpenAiConfiguration from a dictionary of settings.
        Parameters:
            settings (dict): Dictionary containing 'ApiKey' and 'Model' keys.
        Returns:
            Result[OpenAiConfiguration]: Result object containing OpenAiConfiguration or error message.
        '''
        try:
            return Result.ok(OpenAiConfiguration(
                api_key=settings.get("ApiKey", ""),
                model=settings.get("Model", "gpt-4o"),
                max_tokens=settings.get("MaxTokens", 200),
                temperature=settings.get("Temperature", 0.2)
            ))
        except ValueError as e:
            return Result.err(f"Invalid OpenAI settings: {e}")