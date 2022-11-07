sEQE-Control-Software
=====================

Software to control sensitive external quantum efficiency setup in AFMD Group. The setup is currently running on Linux but is being made compatible with Windows. Mac compatibility will be tested in the future.

#############
Prerequisites
#############

1. Proprietary software needed: 

- Lock-in Amplifier: LabOne by Zurich Instruments which can be downloaded for free at [Zurich Instruments download center](https://www.zhinst.com/europe/en/support/download-center)

- Cryostate: LINK by Linkam Scientific which has to be bought from [Linkam Scientific](https://www.linkam.co.uk/)

############
Installation
############

1. Clone the git repository

2. Install requirements

    `pip install -r requirements.txt`

#####
Usage
#####

3. Navigate to sEQE folder and run script

    `cd [PATH_TO_FOLDER]`

    `python sEQE.py`
