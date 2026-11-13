"""takeover-v1 compatible capability extension; serialization is not physics proof."""

from copy import deepcopy

from pydantic import ValidationError
import pytest

from tree_planner.contracts import Attenuation, ScenarioInput
from test_regressions import input_data


def winter_input():
    data = input_data()
    case = deepcopy(data['evaluation_cases'][0])
    case.update(case_id='winter', role='winter_check', profile_state='leaf_off')
    data['evaluation_cases'].append(case)
    data['constraints']['winter_limits'] = [dict(case_id='winter', target_id=None, maximum_loss_m2_h=2)]
    return data


def test_fixed_crossing_is_explicit_bounded_and_opaque_has_no_coefficient():
    assert Attenuation.model_validate(dict(mode='fixed_crossing', transmission=0.5)).transmission == 0.5
    for data in [dict(mode='fixed_crossing'), dict(mode='fixed_crossing', transmission=-0.1),
                 dict(mode='fixed_crossing', transmission=1.1), dict(mode='opaque', transmission=0.5),
                 dict(mode='path_length', transmission=0.5)]:
        with pytest.raises(ValidationError):
            Attenuation.model_validate(data)


def test_winter_limit_resolves_case_role_and_target_and_cannot_duplicate():
    assert ScenarioInput.model_validate(winter_input()).constraints.winter_limits
    for field, value in [('case_id', 'absent'), ('case_id', 'summer'), ('target_id', 'absent')]:
        data = winter_input()
        data['constraints']['winter_limits'][0][field] = value
        with pytest.raises(ValidationError):
            ScenarioInput.model_validate(data)
    data = winter_input()
    data['constraints']['winter_limits'] *= 2
    with pytest.raises(ValidationError):
        ScenarioInput.model_validate(data)
