from dataclasses import dataclass
import dataclasses

from core import Result


@dataclass(frozen=True)
class QwenCoder30bConfiguration:
    '''
    Configuration for the Qwen Coder 30B model.
    '''
    url: str
    api_key: str
    # Model identifier exposed by the local OpenAI-compatible server
    model: str = dataclasses.field(default="qwen/qwen-coder-30b-instruct", init=False)
    max_tokens: int = 2000
    temperature: float|None = 0.2
    top_p: float|None = 1.0
    timeout: int = 60  # Timeout in seconds for API requests
    headers: dict|None = None  # Additional headers for API requests

    @staticmethod
    def from_dict(config: dict) -> Result['QwenCoder30bConfiguration']:
        '''
        Create a QwenCoder30bConfiguration from a dictionary of settings.
        Parameters:
            settings (dict): Dictionary containing 'ApiKey' and connection settings.
        Returns:
            Result[QwenCoder30bConfiguration]: Result object containing configuration or error message.
        '''
        try:
            return Result.ok(QwenCoder30bConfiguration(
                url=config.get("Url", ""),
                api_key=config.get("ApiKey", ""),
                max_tokens=config.get("MaxTokens", 2000),
                temperature=config.get("Temperature", None),
                top_p=config.get("TopP", None),
                timeout=config.get("Timeout", 60),
                headers=config.get("Headers", None)
            ))
        except ValueError as e:
            return Result.err(f"Invalid Qwen Coder settings: {e}")
