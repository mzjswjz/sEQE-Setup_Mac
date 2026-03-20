# sEQE Setup for Mac

Complete software suite for controlling and analyzing sensitive EQE (sEQE) measurements on macOS (also supports Linux and Windows).

## Repository Structure

```
├── sEQE-Control-Software/      # Hardware control software
├── sEQE-Analysis-Software/     # Data analysis software
├── docs/                        # Documentation
├── requirements_Mac.txt         # macOS Python dependencies
├── requirements_linux.txt       # Linux Python dependencies
└── requirements_windows.txt     # Windows Python dependencies
```

## sEQE-Control-Software

Files for controlling sEQE measurement hardware:

| File | Description |
|------|-------------|
| `sEQE.py` | Main control script — orchestrates measurements, handles data acquisition |
| `monochromator.py` | Monochromator control functions (wavelength selection, grating control) |
| `lockin.py` | Lock-in amplifier interface for signal detection |
| `GUI_V3.ui` | Qt UI layout file for the control interface |
| `GUI_template.py` | Generated Python GUI code from UI file |
| `FDS100-CAL.xlsx` | Calibration data for FDS100 photodiode |
| `FGA21-CAL.xlsx` | Calibration data for FGA21 photodiode |
| `Button_on.png` / `Button_off.png` | UI button graphics |

## sEQE-Analysis-Software

Files for analyzing sEQE measurement data:

| File | Description |
|------|-------------|
| `sEQE_Analysis.py` | Main analysis script with GUI — processes raw sEQE data, applies calibrations, calculates EQE |
| `sEQE_Analysis_template.py` | Template/analysis version with extended functionality |
| `GUI.ui` | Qt UI layout file for the analysis interface |
| `calibration_files/` | Directory containing detector and system calibration files |
| `source/` | Source data directory |

## Requirements

Install dependencies for your platform:

```bash
# macOS
pip install -r requirements_Mac.txt

# Linux
pip install -r requirements_linux.txt

# Windows
pip install -r requirements_windows.txt
```

## Usage

1. **Control Software**: Run `sEQE.py` to start the measurement control GUI
2. **Analysis Software**: Run `sEQE_Analysis.py` to process and analyze measurement data

---
*Author: mzjswjz*
