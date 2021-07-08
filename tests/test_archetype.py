import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal
import pytest

from ibsg import archetype


@pytest.mark.parametrize(
    "s,expected_output",
    [
        (pd.Series(["a", "a", "b", "b"]), "a"),
        (pd.Series(["a", "a", "b", np.nan]), "a"),
    ],
)
def test_get_mode_or_first_occurence(s, expected_output):
    output = archetype._get_mode_or_first_occurence(s)
    assert output == expected_output


def test_get_aggregation_operations():
    df = pd.DataFrame(
        {
            "cat": pd.Series(["a", "b", "c"], dtype="category"),
            "str": pd.Series(["a", "b", "c"], dtype=str),
            "obj": pd.Series(["a", "b", "c"], dtype="object"),
            "int": pd.Series([1, 2, 3], dtype="int64"),
            "float": pd.Series([1.1, 2.2, 3.3], dtype="float64"),
        }
    )
    expected_output = {
        "cat": archetype._get_mode_or_first_occurence,
        "str": archetype._get_mode_or_first_occurence,
        "obj": archetype._get_mode_or_first_occurence,
        "int": "median",
        "float": "median",
    }

    output = archetype._get_aggregation_operations(df)

    assert output == expected_output


def test_create_archetypes():
    stock = pd.DataFrame(
        {
            "countyname": 10 * ["Co. Dublin"],
            "dwelling_type": [
                "Detached house",
                "Mid-terrace house",
                "End of terrace house",
                "Detached house",
                "Detached house",
                "End of terrace house",
                "Detached house",
                "Detached house",
                "Ground-floor apartment",
                "Ground-floor apartment",
            ],
            "wall_uvalue": [
                1.83,
                2.09,
                0.60,
                1.77,
                0.28,
                0.37,
                0.30,
                2.00,
                0.50,
                0.94,
            ],
            "main_sh_boiler_fuel": [
                "Heating Oil                   ",
                "Mains Gas                     ",
                "Heating Oil                   ",
                "Heating Oil                   ",
                "Heating Oil                   ",
                "Mains Gas                     ",
                "Heating Oil                   ",
                "Heating Oil                   ",
                "Electricity                   ",
                "Mains Gas                     ",
            ],
        }
    )
    expected_output = pd.DataFrame(
        {
            "dwelling_type": [
                "Detached house",
                "End of terrace house",
                "Ground-floor apartment",
            ],
            "wall_uvalue": [1.77, 0.485, 0.72],
            "main_sh_boiler_fuel": [
                "Heating Oil                   ",
                "Heating Oil                   ",
                "Electricity                   ",
            ],
            "sample_size": [5, 2, 2],
            "archetype": 3 * ["dwelling_type"],
        }
    )
    output = archetype._create_archetypes(
        stock=stock,
        archetype_name="dwelling_type",
        index_columns=["dwelling_type"],
        exclude_columns=["countyname"],
        sample_size=1,
    )
    assert_frame_equal(output, expected_output)


def test_flag_known_buildings():
    stock = pd.DataFrame(
        {
            "dwelling_type": [
                "Detached house",
                "End of terrace house",
                "Ground-floor apartment",
            ],
            "wall_uvalue": [1.77, 0.485, np.nan],
        }
    )
    expected_output = pd.DataFrame(
        {
            "dwelling_type": [
                "Detached house",
                "End of terrace house",
                "Ground-floor apartment",
            ],
            "wall_uvalue": [1.77, 0.485, np.nan],
            "archetype": ["none", "none", np.nan],
        }
    )
    output = archetype._flag_known_buildings(stock=stock, on_column="wall_uvalue")
    assert_frame_equal(output, expected_output)


def test_fillna_with_archetypes():
    stock = pd.DataFrame(
        {
            "dwelling_type": [
                "Detached house",
                "Mid-terrace house",
                "End of terrace house",
                "Detached house",
                "Detached house",
                "End of terrace house",
                "Detached house",
                "Detached house",
                "Ground-floor apartment",
                "Ground-floor apartment",
            ],
            "wall_uvalue": [
                np.nan,
                2.09,
                0.60,
                1.77,
                0.28,
                0.37,
                0.30,
                2.00,
                0.50,
                0.94,
            ],
            "main_sh_boiler_fuel": [
                np.nan,
                "Mains Gas                     ",
                "Heating Oil                   ",
                "Heating Oil                   ",
                "Heating Oil                   ",
                "Mains Gas                     ",
                "Heating Oil                   ",
                "Heating Oil                   ",
                "Electricity                   ",
                "Mains Gas                     ",
            ],
            "archetype": [np.nan] + 9 * ["none"],
        }
    )
    archetypes = pd.DataFrame(
        {
            "dwelling_type": [
                "Detached house",
                "End of terrace house",
                "Ground-floor apartment",
            ],
            "wall_uvalue": [1.77, 0.485, 0.72],
            "main_sh_boiler_fuel": [
                "Heating Oil                   ",
                "Heating Oil                   ",
                "Electricity                   ",
            ],
            "sample_size": [5, 2, 2],
            "archetype": 3 * ["dwelling_type"],
        }
    )
    # pd.DataFrame.combine_first() sorts index values by default
    # ... so shuffles input DataFrame when filling with archetypes
    expected_output = pd.DataFrame(
        {
            "dwelling_type": [
                "Detached house",
                "Detached house",
                "Detached house",
                "Detached house",
                "Detached house",
                "End of terrace house",
                "End of terrace house",
                "Ground-floor apartment",
                "Ground-floor apartment",
                "Mid-terrace house",
            ],
            "archetype": ["dwelling_type"] + 9 * ["none"],
            "main_sh_boiler_fuel": [
                "Heating Oil                   ",
                "Heating Oil                   ",
                "Heating Oil                   ",
                "Heating Oil                   ",
                "Heating Oil                   ",
                "Heating Oil                   ",
                "Mains Gas                     ",
                "Electricity                   ",
                "Mains Gas                     ",
                "Mains Gas                     ",
            ],
            "sample_size": [5.0, 5.0, 5.0, 5.0, 5.0, 2.0, 2.0, 2.0, 2.0, np.nan],
            "wall_uvalue": [1.77, 1.77, 0.28, 0.3, 2.0, 0.6, 0.37, 0.5, 0.94, 2.09],
        }
    )
    output = archetype._fillna_with_archetypes(
        stock=stock, archetypes=archetypes, archetype_columns=["dwelling_type"]
    )
    assert_frame_equal(output, expected_output, check_like=True)