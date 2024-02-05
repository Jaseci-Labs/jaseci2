from fastapi import FastAPI as _FaststAPI

from uvicorn import run as _run


class FastAPI:
    __app__ = None

    @classmethod
    def get(cls) -> _FaststAPI:
        if not isinstance(cls.__app__, _FaststAPI):
            cls.__app__ = _FaststAPI()
            cls.walker_get = cls.__app__.get
            cls.walker_post = cls.__app__.post
            cls.walker_put = cls.__app__.put
            cls.walker_patch = cls.__app__.patch
            cls.walker_delete = cls.__app__.delete
            cls.walker_head = cls.__app__.head
            cls.walker_options = cls.__app__.options
            cls.walker_trace = cls.__app__.trace

            from jaclang_fastapi.routers import user_router

            cls.__app__.include_router(user_router)

        return cls.__app__

    @classmethod
    def start(
        cls, host: str = "0.0.0.0", port: int = 8000, **kwargs
    ) -> None:  # noqa: ANN003
        """Not Available Yet."""
        _run(cls.get(), host=host, port=port, **kwargs)
