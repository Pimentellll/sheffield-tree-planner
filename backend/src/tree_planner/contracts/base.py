"""Strict, immutable wire primitives. No numerical solver or runtime permissions."""

from datetime import date, datetime
import re
from typing import Annotated, TypeVar

from pydantic import AfterValidator, BaseModel, BeforeValidator, ConfigDict, Field

SCHEMA_VERSION = "0.1.0"


class ContractModel(BaseModel):
    model_config = ConfigDict(
        strict=True, extra="forbid", frozen=True, allow_inf_nan=False, validate_default=True
    )


def array(value):
    # HTTP JSON arrays and Python model_dump(mode='json') have identical meaning.
    # Never coerce arbitrary iterables, strings, sets or mappings into arrays.
    return tuple(value) if type(value) is list else value


class FrozenDict(dict):
    def _immutable(self, *args, **kwargs):
        raise TypeError("immutable contract mapping")

    __setitem__ = __delitem__ = clear = pop = popitem = setdefault = update = __ior__ = _immutable


T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")
Array = Annotated[tuple[T, ...], BeforeValidator(array)]
Map = Annotated[dict[K, V], AfterValidator(FrozenDict)]
ID = Annotated[str, Field(min_length=1, pattern=r"\S")]
Revision = Annotated[int, Field(gt=0)]
NonnegativeInt = Annotated[int, Field(ge=0)]
Positive = Annotated[float, Field(gt=0)]
Nonnegative = Annotated[float, Field(ge=0)]
Vec3 = Annotated[tuple[float, float, float], BeforeValidator(array)]
Radii = Annotated[tuple[Positive, Positive, Positive], BeforeValidator(array)]
Hash = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]


def utc(value: str) -> str:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z", value):
        raise ValueError("UTC timestamp must end in literal Z and include seconds")
    datetime.fromisoformat(value[:-1] + "+00:00")
    return value


def calendar_date(value: str) -> str:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError("expected YYYY-MM-DD")
    date.fromisoformat(value)
    return value


UTC = Annotated[
    str, AfterValidator(utc), Field(pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,6})?Z$")
]
Date = Annotated[str, AfterValidator(calendar_date), Field(pattern=r"^\d{4}-\d{2}-\d{2}$")]


def unique(values, label):
    if len(values) != len(set(values)):
        raise ValueError(f"duplicate {label}")


def matrix(value):
    rows = array(value)
    if type(rows) is tuple:
        return tuple(array(row) for row in rows)
    return rows


Row4 = tuple[float, float, float, float]


def invertible(rows):
    # Gaussian elimination with pivoting; no scientific tolerance is invented here.
    work = [list(row) for row in rows]
    for col in range(4):
        pivot = max(range(col, 4), key=lambda i: abs(work[i][col]))
        if work[pivot][col] == 0:
            raise ValueError("matrix must be invertible")
        work[col], work[pivot] = work[pivot], work[col]
        for row in range(col + 1, 4):
            ratio = work[row][col] / work[col][col]
            for k in range(col + 1, 4):
                work[row][k] -= ratio * work[col][k]
    return rows


Matrix4 = Annotated[
    tuple[Row4, Row4, Row4, Row4], BeforeValidator(matrix), AfterValidator(invertible)
]
