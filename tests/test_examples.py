from io import StringIO

import pytest

from wtdtk.names import (
    BiopsyModality,
    BiopsySample,
    Disease,
    SectionDetails,
    SectionModality,
    SectionSample,
    VibratomeModality,
    VibratomeSample,
)
from wtdtk.section_table import read_sections_csv, write_sections_csv


@pytest.mark.parametrize(
    ("slug", "disease", "patient", "biopsy", "modality"),
    [
        ("T-P1-B1-MRE", Disease.TNBC, 1, 1, BiopsyModality.MRE),
        ("H-P1-B1-MRI", Disease.HCC, 1, 1, BiopsyModality.MRI),
    ],
)
def test_biopsy_slugs(slug, disease, patient, biopsy, modality):
    parsed = BiopsySample.from_str(slug)
    assert parsed.biopsy.disease_code == disease
    assert parsed.biopsy.patient_idx == patient
    assert parsed.biopsy.biopsy_idx == biopsy
    assert parsed.modality == modality
    assert slug == str(parsed)


@pytest.mark.parametrize(
    ("slug", "disease", "patient", "biopsy", "vibratome", "modality"),
    [
        ("T-P1-B1-V1-EVMRE", Disease.TNBC, 1, 1, 1, VibratomeModality.EVMRE),
        ("H-P21-B2-V1-RC", Disease.HCC, 21, 2, 1, VibratomeModality.RC),
        ("L-P5-B1-V2-RPT", Disease.ILD, 5, 1, 2, VibratomeModality.RPT),
        ("H-P1-B2-V1-2P", Disease.HCC, 1, 2, 1, VibratomeModality.TwoP),
    ],
)
def test_vibratome_slugs(slug, disease, patient, biopsy, vibratome, modality):
    parsed = VibratomeSample.from_str(slug)
    assert parsed.vibratome.biopsy.disease_code == disease
    assert parsed.vibratome.biopsy.patient_idx == patient
    assert parsed.vibratome.biopsy.biopsy_idx == biopsy
    assert parsed.vibratome.vibratome_section == vibratome
    assert parsed.modality == modality
    assert slug == str(parsed)


@pytest.mark.parametrize(
    ("slug", "disease", "patient", "biopsy", "vibratome", "section", "modality"),
    [
        ("T-P1-B1-V1-S1-HE", Disease.TNBC, 1, 1, 1, 1, SectionModality.HE),
        ("H-P2-B2-V2-S2-ST", Disease.HCC, 2, 2, 2, 2, SectionModality.ST),
        ("L-P31-B3-V1-S4-DS", Disease.ILD, 31, 3, 1, 4, SectionModality.DS),
        ("H-P1-B1-V3-S2-FD", Disease.HCC, 1, 1, 3, 2, SectionModality.FD),
        ("L-P23-B3-V1-S2-FP", Disease.ILD, 23, 3, 1, 2, SectionModality.FP),
        ("L-P31-B3-V1-S4-LA", Disease.ILD, 31, 3, 1, 4, SectionModality.LA),
        ("H-P2-B1-V2-S3-PR", Disease.HCC, 2, 1, 2, 3, SectionModality.PR),
    ],
)
def test_section_slugs(slug, disease, patient, biopsy, vibratome, section, modality):
    parsed = SectionSample.from_str(slug)
    assert parsed.section.biopsy.disease_code == disease
    assert parsed.section.biopsy.patient_idx == patient
    assert parsed.section.biopsy.biopsy_idx == biopsy
    assert parsed.section.vibratome_section == vibratome
    assert parsed.section.serial_section == section
    assert parsed.modality == modality
    assert slug == str(parsed)


CSV_STR = """
Serial number,Modality,Thickness (um),Substrate
1,spare,10,Glass
2,spare,10,Glass
3,HE,5,Glass
4,RC/DS/LA,10,Ca2F
5,ST/FD/FP/HE,5,Xenium
6,PR,10,Glass
7,spare,10,Glass
8,spare,10,Glass
9,spare,10,Glass
""".lstrip()


def test_parse_csv():
    lines = CSV_STR.splitlines()
    details = list(read_sections_csv(lines))

    assert details[0] == SectionDetails(1, [], 10, "Glass")
    assert details[3] == SectionDetails(
        4, [SectionModality.RC, SectionModality.DS, SectionModality.LA], 10, "Ca2F"
    )
    assert details[5] == SectionDetails(6, [SectionModality.PR], 10, "Glass")


def test_write_csv():
    details = list(read_sections_csv(CSV_STR.splitlines()))
    sio = StringIO()
    write_sections_csv(sio, details)
    details2 = list(read_sections_csv(sio.getvalue().splitlines()))
    assert details2 == details
