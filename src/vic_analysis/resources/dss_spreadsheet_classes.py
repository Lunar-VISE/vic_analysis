# Built-Ins
import re
from dataclasses import dataclass
from enum import IntFlag, auto

import pandas as pd

# Dependencies
from pydantic import BaseModel, model_validator

# Top-Level Import
from vic_analysis.detector_specs import BandName


def make_empty_set() -> dict[BandName, float]:
    empty_set: dict[BandName, float] = {
        "Filter1": 0,
        "Filter2": 0,
        "Filter3": 0,
        "Filter4": 0,
        "Filter5": 0,
        "Filter6": 0,
        "Filter7": 0,
    }
    return empty_set


def make_empty_list_set() -> dict[BandName, list[float]]:
    empty_list_set: dict[BandName, list[float]] = {
        "Filter1": [],
        "Filter2": [],
        "Filter3": [],
        "Filter4": [],
        "Filter5": [],
        "Filter6": [],
        "Filter7": [],
    }
    return empty_list_set


class LampStateTable(BaseModel):
    measurement_id: str
    cxr_file: str
    lamp_state: int
    lamps_on: list[int]
    dss_va_state: float
    band_center: dict[BandName, float]
    band_rdn: dict[BandName, float]
    band_albedo: dict[BandName, float]

    @classmethod
    def empty(cls) -> "LampStateTable":
        empty_set = make_empty_set()
        return cls(
            measurement_id="VIC0_000_00%",
            cxr_file="empty",
            lamp_state=0,
            lamps_on=[],
            dss_va_state=0,
            band_center=empty_set,
            band_rdn=empty_set,
            band_albedo=empty_set,
        )

    @model_validator(mode="after")
    def check_id_formats(self) -> "LampStateTable":
        measurement_id_pattern = r"VIC\d_\d{3}_\d(?:\.?\d)?%"
        measid_match = re.match(measurement_id_pattern, self.measurement_id)
        if measid_match is None:
            raise ValueError(f"Measurement ID is invalid: {self.measurement_id}")
        return self


class LampFlags(IntFlag):
    NoLamps = 0
    Lamp1 = auto()
    Lamp2 = auto()
    Lamp3 = auto()
    Lamp4 = auto()
    Lamp5 = auto()
    Lamp6 = auto()
    Lamp7 = auto()
    Lamp8 = auto()


INTDEX_TO_FLAG = {
    1: LampFlags.Lamp1,
    2: LampFlags.Lamp2,
    3: LampFlags.Lamp3,
    4: LampFlags.Lamp4,
    5: LampFlags.Lamp5,
    6: LampFlags.Lamp6,
    7: LampFlags.Lamp7,
    8: LampFlags.Lamp8,
}


def encode_lamp_state(lamp_on_list: list[int], dss_va_state: int) -> int:
    """
    Step 1: Binary Encoding of Lamp State
    The DSS Lamp list is encoded to a single binary integer where the number
    of lamp that is turned on represents the position (indexed from 1) in
    the binary string.

    For example, if lamps 1, 2, 4 and 8 are on, the binary string and
    corresponding 8-bit integer ID would be:

    [8(on),7(off),6(off),5(off),4(on),3(off),2(on),1(on)] --> 10001011 --> 139

    Step 2: Bit-Packing to combine dss va state and lamp state
    The lamp state integer is left bit-shifted by 7 bits to make room for the
    7-bit number representing the va state (0-100). The final number is a
    15-bit integer.

    Parameters
    ----------
    lamp_on_list: list[int]
        List of the lamps that are on (1-8).
    dss_va_state: int
        VA State from 0-100(%).

    Returns
    -------
    integer_id: int
        Integer ID corresponding to the correct lamp and VA state.
    """
    # Validation of args
    if not 0 <= dss_va_state <= 100:
        raise ValueError(f"DSS VA State is not between 0 and 100. ({dss_va_state})")
    lamp_flag = LampFlags.NoLamps
    for i in lamp_on_list:
        lamp_flag |= INTDEX_TO_FLAG[i]

    integer_id = (lamp_flag << 7) | dss_va_state
    print(integer_id, lamp_on_list, dss_va_state)

    return integer_id


def decode_lamp_state(integer_id: int) -> tuple[LampFlags, int]:
    """
    Decodes a lamp state integer ID. Returns a list of lamps that are turned on
    in this lamp state (1-8) as well as the VA state.

    See `encode_lamp_state` for more information.

    Parameters
    ----------
    integer_id: int
        Integer lamp state ID.

    Returns
    -------
    lamp_list: list[int]
        List of lamps that are turned on in this lamp state.
    """
    dss_va_state_mask = (1 << 7) - 1

    va_state = integer_id & dss_va_state_mask
    flags = LampFlags(integer_id >> 7)

    return flags, va_state


@dataclass
class ExcelData:
    config: pd.DataFrame
    cxr: pd.DataFrame
    response: pd.DataFrame
    solar: pd.DataFrame
