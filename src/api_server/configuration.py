import dataclasses

from core import Result

__DEFAULT_FASTAPI_PORT__ = 8000
__DEFAULT_FASTAPI_HOST__ = "0.0.0.0"

@dataclasses.dataclass(frozen=True)
class FastApiConfiguration:
    port: int
    host: str

    @staticmethod
    def from_dict(settings: dict) -> Result['FastApiConfiguration']:
        try:
            return Result.ok(FastApiConfiguration(
                port=settings.get("Port", __DEFAULT_FASTAPI_PORT__),
                host=settings.get("Host", __DEFAULT_FASTAPI_HOST__)
            ))
        except ValueError as e:
            return Result.err(f"Invalid FastAPI settings: {e}")