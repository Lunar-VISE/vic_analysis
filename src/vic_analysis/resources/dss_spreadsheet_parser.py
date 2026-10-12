# Built-Ins
from pathlib import Path

# Dependencies
import numpy as np
import pandas as pd
from scipy.interpolate import PchipInterpolator

# Top-Level Imports
from vic_analysis.detector_specs import BandName, band_names

# Relative Imports
from .dss_spreadsheet_classes import (
    ExcelData,
    LampStateTable,
    make_empty_list_set,
    make_empty_set,
)


def get_data_from_xl(xlfp: str) -> ExcelData:
    config = pd.read_excel(
        xlfp,
        sheet_name="DSS Config Table",
        header=2,
    )

    cxr_spectra = pd.read_excel(
        xlfp, sheet_name="CXR spectra", header=0, skiprows=(1, 2)
    )
    cxr_spectra.rename(columns={"File =>": "wvl(nm)"}, inplace=True)

    filter_response = pd.read_excel(
        xlfp, sheet_name="VIC RSRs (1nm sampling)", header=2
    )

    solar = pd.read_excel(xlfp, sheet_name="VIC RSR-weighted Solar Radiance", header=3)

    return ExcelData(
        config=config, cxr=cxr_spectra, response=filter_response, solar=solar
    )


def get_band_response(
    excel_data: ExcelData, band: BandName
) -> tuple[np.ndarray, np.ndarray]:
    wvl = excel_data.response["wvl(nm)"].to_numpy()
    response = excel_data.response[f"RSR_Band{band[-1]}"].to_numpy()
    return wvl, response


def get_cxr_measurement(excel_data: ExcelData, measurement_name: str):
    wvl = excel_data.cxr["wvl(nm)"].to_numpy()
    meas = excel_data.cxr[measurement_name].to_numpy()
    return wvl, meas


def get_solar(excel_data: ExcelData) -> tuple[np.ndarray, np.ndarray]:
    solar_wvl = excel_data.solar["nm"].to_numpy()
    solar_spec = excel_data.solar["Scene Radiance (mw/m^2-nm-sr)"].to_numpy()
    return solar_wvl, solar_spec


def get_band_solar_radiance(excel_data: ExcelData, band: BandName) -> float:
    response_wvl, response = get_band_response(excel_data, band)
    solar_wvl, solar_spec = get_solar(excel_data)

    interp = PchipInterpolator(solar_wvl, solar_spec)
    solar_interp = interp(response_wvl)

    return float(np.average(solar_interp, weights=response))


def get_band_center(excel_data: ExcelData, band: BandName) -> float:
    response_wvl, response = get_band_response(excel_data, band)
    return float(np.average(response_wvl, weights=response))


def get_band_radiance(
    excel_data: ExcelData, band: BandName, measurement_name: str
) -> float:
    _wvl, cxr = get_cxr_measurement(excel_data, measurement_name)
    _response_wvl, response = get_band_response(excel_data, band)
    return float(np.average(cxr, weights=response))


def search_cxr_cal_directory(cxr_dir: str | Path, lamp_state: int):
    band_radiances = make_empty_set()
    band_albedos = make_empty_set()
    band_rdn_lists = make_empty_list_set()
    band_albedo_lists = make_empty_list_set()
    for i in Path(cxr_dir).iterdir():
        with open(i) as f:
            json = f.read()
        meas = LampStateTable.model_validate_json(json)
        if meas.lamp_state != lamp_state:
            continue

        for band in band_names:
            band_rdn_lists[band].append(meas.band_rdn[band])
            band_albedo_lists[band].append(meas.band_albedo[band])

        for k, v in band_rdn_lists.items():
            band_radiances[k] = float(np.mean(v))
        for k, v in band_albedo_lists.items():
            band_albedos[k] = float(np.mean(v))

    return band_radiances, band_albedos


def get_all_radiances_for_band(
    cxr_dir: str | Path, band: BandName, quiet: bool = False
):
    all_radiances = {}
    all_albedos = {}
    lamp_id_translator = {}

    for i in Path(cxr_dir).iterdir():
        with open(i) as f:
            json = f.read()
        meas = LampStateTable.model_validate_json(json)
        lamp_id_translator[meas.measurement_id] = meas.lamp_state

    if not quiet:
        print(f"Radiances achieved in {band}\n----------")
    for k, v in lamp_id_translator.items():
        band_rdn, band_alb = search_cxr_cal_directory(cxr_dir, v)
        all_radiances[k] = band_rdn[band]
        all_albedos[k] = band_alb[band]
        if not quiet:
            print(f"{k} -- {v} -- {band_rdn[band]}")

    return all_radiances, all_albedos
