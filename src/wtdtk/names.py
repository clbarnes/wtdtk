"""Utilities for parsing and serialising sample names and disease/ modality codes."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import StrEnum
from typing import Self

logger = logging.getLogger(__name__)


class Disease(StrEnum):
    """Code for disease."""

    TNBC = "T"
    """Triple negative breast cancer"""

    HCC = "H"
    """Hepatocellular carcinoma"""

    ILD = "L"
    """Interstitial lung disease"""


@dataclass(order=True, frozen=True)
class BiopsyID:
    """Parsed biopsy identifier. Use `str(biopsy_id)` to serialise."""

    disease_code: Disease
    """Disease sample this biopsy comes from."""
    patient_idx: int
    """Patient index; only unique in the context of this disease."""
    biopsy_idx: int
    """Biopsy index."""

    def __str__(self) -> str:
        return f"{self.disease_code}-P{self.patient_idx}-B{self.biopsy_idx}"

    @classmethod
    def from_str(cls, s: str) -> Self:
        """Parse a biopsy identifier string."""
        dc, pi, bi, *others = s.split("-")
        if others:
            raise ValueError(f"Found extra fields while deserializing: {others}")
        dis = Disease(dc)
        if not pi.startswith("P"):
            raise ValueError(f"Expected P-prefixed patient index, got {pi!r}")
        p = int(pi[1:])
        if not bi.startswith("B"):
            raise ValueError(f"Expected B-prefixed biopsy index, got {bi!r}")
        b = int(bi[1:])
        return cls(dis, p, b)


class BiopsyModality(StrEnum):
    """Modalities applied to whole biopsies or live patients."""

    MRE = "MRE"
    """Magnetic resonance elastography"""

    MRI = "MRI"
    """Magnetic resonance imaging"""


@dataclass(order=True, frozen=True)
class BiopsySample:
    """Single modality sample from a particular biopsy."""

    biopsy: BiopsyID
    """Identifier of the source biopsy."""
    modality: BiopsyModality
    """Modality of the sample."""

    def __str__(self) -> str:
        return f"{self.biopsy}-{self.modality}"

    @classmethod
    def from_str(cls, s: str) -> Self:
        """Parse the biopsy sample identifier string."""
        biop_str, mod_str = s.rsplit("-", maxsplit=1)
        biopsy = BiopsyID.from_str(biop_str)
        return cls(biopsy, BiopsyModality(mod_str))


class VibratomeModality(StrEnum):
    """Imaging modalities applied to live samples."""

    EVMRE = "EVMRE"
    """Ex-vivo elastography"""

    RC = "RC"
    """Raman confocal"""

    RPT = "RPT"
    # TODO: projection tomography?
    """Raman spectral proj tomo"""

    TwoP = "2P"
    """Two photon.

    N.B. this is the only modality where the enum value '2P' does not equal the name 'TwoP',
    because of python restrictions on variable naming.
    """


@dataclass(order=True, frozen=True)
class VibratomeID:
    """Identifier for the vibratome section."""

    biopsy: BiopsyID
    """Source biopsy for the vibratome section."""
    vibratome_section: int
    """Index of the vibratome section."""

    def __str__(self) -> str:
        return f"{self.biopsy}-V{self.vibratome_section}"

    @classmethod
    def from_str(cls, s: str) -> Self:
        """Parse a vibratome section identifier."""
        biop_str, vi = s.rsplit("-", 1)
        biopsy = BiopsyID.from_str(biop_str)
        if not vi.startswith("V"):
            raise ValueError(f"Expected V-prefixed vibratome section, got {vi!r}")
        v = int(vi[1:])
        return cls(biopsy, v)


@dataclass(order=True, frozen=True)
class VibratomeSample:
    """Single modality sample from a particular vibratome section."""

    vibratome: VibratomeID
    """Identifier of the source vibratome section."""
    modality: VibratomeModality
    """Modality of the sample."""

    def __str__(self) -> str:
        return f"{self.vibratome}-{self.modality}"

    @classmethod
    def from_str(cls, s: str) -> Self:
        """Parse a vibratome sample identifier string."""
        vib_str, mod_str = s.rsplit("-", 1)
        vibratome = VibratomeID.from_str(vib_str)
        return cls(vibratome, VibratomeModality(mod_str))


@dataclass(order=True, frozen=True)
class SectionID(VibratomeID):
    """Identifier for a fixed serial section cut from a vibratome section."""

    vibratome: VibratomeID
    """Source vibratome section for the serial section."""
    serial_section: int
    """Index of the serial section within the vibratome section."""

    def __str__(self) -> str:
        return f"{self.vibratome}-S{self.serial_section}"

    @classmethod
    def from_str(cls, s: str) -> Self:
        """Parse a serial section identifier string."""
        vib_str, si = s.rsplit("-", 1)
        vibratome = VibratomeID.from_str(vib_str)
        if not si.startswith("S"):
            raise ValueError(f"Expected S-prefixed serial section, got {si!r}")
        serial = int(si[1:])
        return cls(vibratome.biopsy, vibratome.vibratome_section, vibratome, serial)


class SectionModality(StrEnum):
    """Imaging modalities applied to fixed sections."""

    HE = "HE"
    """H&E"""

    ST = "ST"
    """Spatial transcriptomics"""

    RC = "RC"
    """Raman confocal"""

    DS = "DS"
    """DESI-MS"""

    FD = "FD"
    # TODO: diffraction?
    """Flash paint diff limit"""

    FP = "FP"
    """Flash paint (high res)"""

    LA = "LA"
    """LA-ICP-MS"""

    PR = "PR"
    """Spatial proteomics"""


@dataclass(order=True, frozen=True)
class SectionSample:
    """Single modality sample from a particular serial section."""

    section: SectionID
    """Identifier of the source serial section."""
    modality: SectionModality
    """Modality of the sample."""

    def __str__(self) -> str:
        return f"{self.section}-{self.modality}"

    @classmethod
    def from_str(cls, s: str) -> Self:
        """Parse a section sample identifier string."""
        sec_str, mod_str = s.rsplit("-", 1)
        section = SectionID.from_str(sec_str)
        return cls(section, SectionModality(mod_str))


@dataclass(order=True, frozen=True)
class SectionDetails:
    """Details of sections taken from a single biopsy which is fixed post-live imaging."""

    serial_number: int
    """Serial section index."""
    modality: list[SectionModality]
    """Modalities applied to this section; empty if the section is spare."""
    thickness: float
    """In micrometers"""
    substrate: str
    """Substrate the section is mounted on, e.g. "Glass"."""

    def to_row(self) -> list[str]:
        """Serialise to a list of strings, e.g. to write to a CSV."""
        mod = " / ".join(self.modality) if self.modality else "spare"
        return [
            str(self.serial_number),
            mod,
            str(self.thickness),
            self.substrate,
        ]

    @classmethod
    def from_row(cls, cells: list[str]) -> Self:
        """Parse from a list of strings, e.g. from a CSV."""
        ser_cell, mod_cell, thick_cell, subs_cell, *other = (s.strip() for s in cells)
        ser = int(ser_cell)
        mod = []
        if mod_cell.lower() != "spare":
            for s in mod_cell.upper().split("/"):
                s = s.strip()
                mod_item = SectionModality(s)
                mod.append(mod_item)

        if other:
            logger.debug("ignoring additional cells: %s", other)

        return cls(ser, mod, float(thick_cell), subs_cell)

    @classmethod
    def headers(cls) -> list[str]:
        """Headers of a CSV containing the section information."""
        return ["Serial number", "Modality", "Thickness (um)", "Substrate"]
