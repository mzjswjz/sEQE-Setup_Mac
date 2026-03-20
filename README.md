# sEQE Setup (Mac)

Setup and analysis scripts for spectral external quantum efficiency (sEQE) measurements on macOS.

## Overview

sEQE (spectral external quantum efficiency) measurements characterize how efficiently a solar cell converts photons of different wavelengths into electrical current. This repository provides:

- Measurement setup scripts
- Data acquisition utilities
- Analysis tools for sEQE data

## What is sEQE?

External quantum efficiency (EQE) measures the ratio of collected charge carriers to incident photons at each wavelength:

```
EQE(λ) = J_SC(λ) / (q × φ_ph(λ))
```

Where:
- J_SC(λ) = Short-circuit current at wavelength λ
- q = Elementary charge
- φ_ph(λ) = Incident photon flux

The "s" prefix typically indicates "spectral" - measuring EQE across the solar spectrum.

## Setup Components

### Hardware
- Monochromator
- Light source (tungsten/halogen or xenon)
- Current amplifier
- Lock-in amplifier
- Reference detector

### Software
- Data acquisition (National Instruments/Thorlabs)
- Python-based analysis pipeline
- Plotting and reporting tools

## Measurement Procedure

1. **Calibration** - Measure reference detector response
2. **Sample Measurement** - Measure device under test
3. **Dark Measurement** - Subtract background
4. **Calculate EQE** - Compute spectral response

## Data Analysis

The analysis includes:
- Wavelength-dependent response
- Integration with AM1.5G spectrum
- J_SC calculation
- Comparison with device simulations

## Usage

```python
python seqe_measure.py --config config.yaml
python seqe_analyze.py --input data.csv
```

## Dependencies

- NumPy
- SciPy
- Matplotlib
- pandas
- PyDAQmx (if using NI hardware)

## Author

mzjswjz
