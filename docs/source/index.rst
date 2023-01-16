.. sEQE-Control-Software documentation master file, created by
   sphinx-quickstart on Tue Oct 11 11:42:15 2022.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to the documentation of AFMD's sEQE setup !
===========================================================================================

The documentation contains the full hardware, software and handling requirements to rebuild and use the sensitive external quantum efficiency (sEQE) setup of the AFMD Group.


What is this Project about ?
----------------------------
This project is about a common technique in solar cell research to probe a solar cell's photocurrent upon illumination. The measured photocurrent can be used to calculate the so called external quantum efficiency (EQE) of the solar cell, which is a parameter for the solar cells performance. (TODO: for example with our sEQE-Analysis Program - Build reference):
	
.. math::
	\text{EQE} = \frac{\text{electron-hole pairs per sec}}{\text{photons per sec}}

For further background knowledge the interested reader is refered to:  

1. `Who is the AFMD group ? <https://www.physics.ox.ac.uk/research/group/advanced-functional-materials-and-devices-afmd-group>`_

2. `What is a Solar cell ? <https://en.wikipedia.org/wiki/Solar_cell>`_

3. `Why do we measure EQE ? <https://en.wikipedia.org/wiki/Quantum_efficiency#Quantum_efficiency_of_solar_cells>`_

The sEQE setup is an experimental setup built by Dr. Anna Jungbluth to provide a research group with the means to evaluate one of their own solar cell device's performance parameters. It is capable of reaching an EQE sensitivity of :math:`10^{-6}`.



Where is this Project going ? 
-----------------------------
The sEQE setup is maintained by the AFMD group and they have many ideas for its future development. Some of those which are already in work are:

1. Integrating and automating a cryostate

2. Integrating a light bias source

Feel free to reach out to the AFMD group if you have any ideas for further improvement or feedback.

.. toctree::
   :maxdepth: 2
   :caption: Contents:
   
   content/README
   content/hardware
   content/usage
   control_generated/modules
   analysis_generated/modules
   content/contact
   content/licence
	

Credits
-------
TODO: Mention AFMD members and third party package authors

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
