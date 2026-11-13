from typing import Annotated, Literal

from pydantic import Field, model_serializer, model_validator

from .base import (
    Array,
    ContractModel,
    Date,
    ID,
    Map,
    Nonnegative,
    NonnegativeInt,
    Positive,
    Radii,
    Revision,
    Vec3,
    unique,
)


class Attenuation(ContractModel):
    """takeover-v1 adds a bounded, explicitly assumed fixed-crossing scenario."""

    mode: Literal["opaque", "fixed_crossing"]
    transmission: Annotated[float, Field(ge=0, le=1)] | None = None

    @model_validator(mode="after")
    def coefficient(self):
        if (self.mode == "fixed_crossing") != (self.transmission is not None):
            raise ValueError("only fixed_crossing requires an explicit transmission")
        return self

    @model_serializer(mode="wrap")
    def serialize_attenuation(self, handler):
        data = handler(self)
        if self.mode == "opaque":
            data.pop("transmission", None)
        return data


class TreeState(ContractModel):
    horizon_years: Nonnegative
    leaf_state: ID  # A sourced/assumed label; the draft does not define an enum.
    crown_center_height_m: Nonnegative
    crown_radii_m: Radii
    trunk_radius_m: Positive
    trunk_height_m: Positive
    attenuation: Attenuation


class TreeProfile(ContractModel):
    schema_version: Literal["0.1.0"]
    profile_id: ID
    library_revision: Revision
    species_size_label: ID
    source_ids: Array[ID]
    assumption_ids: Array[ID]
    cost_pence: NonnegativeInt
    cost_scope: ID
    price_date: Date
    states: Map[ID, TreeState]

    @model_validator(mode="after")
    def nonempty_states(self):
        if not self.states:
            raise ValueError("profile must have named states")
        return self


class Placement(ContractModel):
    placement_id: ID
    location_id: ID
    position_enu_m: Vec3
    profile_id: ID
    candidate_id: ID | None
    pinned: bool


class LayoutRef(ContractModel):
    layout_id: ID
    revision: Revision


class Layout(ContractModel):
    schema_version: Literal["0.1.0"]
    layout_id: ID
    revision: Revision
    kind: Literal["existing", "reference", "proposed", "hypothetical"]
    placements: Array[Placement]

    @model_validator(mode="after")
    def distinct(self):
        unique([p.placement_id for p in self.placements], "placement_id")
        unique([p.location_id for p in self.placements], "location_id")
        unique([p.position_enu_m for p in self.placements], "placement position")
        if self.kind == "existing" and self.placements:
            raise ValueError("existing layout has no proposed placements")
        return self
