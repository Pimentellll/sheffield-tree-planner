"""Test-only synthetic JSON boundary; these are not domain contracts."""

import re
from datetime import datetime
from typing import Annotated, Literal

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator


class DefaultProbe(BaseModel):
    """Expose default coercion and extra-field behavior."""

    revision: int


class FrozenProbe(BaseModel):
    """Demonstrate that freezing a model does not freeze its children."""

    model_config = ConfigDict(frozen=True)
    values: list[int]


class StrictTupleProbe(BaseModel):
    """Contrast JSON and Python strict tuple parsing."""

    model_config = ConfigDict(strict=True)
    values: tuple[int, int, int]


class NestedProbe(BaseModel):
    """A deliberately small synthetic nested boundary."""

    model_config = ConfigDict(strict=True, extra="forbid", allow_inf_nan=False)
    vector: Annotated[list[float], Field(min_length=3, max_length=3)]
    value: float


class BoundaryProbe(BaseModel):
    """Synthetic test-only boundary, not a SiteBundle or Scenario."""

    model_config = ConfigDict(strict=True, extra="forbid", allow_inf_nan=False)
    schema_version: Literal["0.1.0"]
    revision: Annotated[int, Field(gt=0)]
    cost_pence: Annotated[int, Field(ge=0)]
    unit: Literal["m"]
    scope: Literal["accepted", "hypothetical"]
    timestamp: str
    nested: NestedProbe
    note: str | None

    @field_validator("timestamp")
    @classmethod
    def require_utc_z(cls, value: str) -> str:
        """Require the probe's exact UTC spelling and a real calendar time."""
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z", value):
            raise ValueError("expected UTC timestamp ending in Z")
        try:
            datetime.fromisoformat(value)
        except ValueError as exc:
            raise ValueError("invalid UTC timestamp") from exc
        return value


def make_app(safe_errors: bool) -> FastAPI:
    """Create an in-process-only test application."""
    application = FastAPI()
    if safe_errors:

        @application.exception_handler(RequestValidationError)
        async def validation_error(
            request: Request, exc: RequestValidationError
        ) -> JSONResponse:
            """Avoid echoing invalid input, including nonfinite values."""
            return JSONResponse(status_code=422, content={"detail": "Invalid request"})

    @application.post("/probe", response_model=BoundaryProbe)
    def probe(body: BoundaryProbe) -> BoundaryProbe:
        """Echo a validated synthetic input for boundary testing."""
        return body

    return application


app = make_app(safe_errors=True)
default_app = make_app(safe_errors=False)
