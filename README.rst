Colorado School of Mines (CSM) Dragonfly modules
================================================
Summary
-------
Dragonfly exposes a Python (currently `Anaconda Python 3.X` <https://www.continuum.io/>`_)
interface that allows for scripting capabilities within the Dragonfly environment. This
enables automated and scriptable access to the many capabilities of Dragonfly, and the
extension of these capabilities through the development of customized routines. This
package provides access to modules developed, or currently under development, at CSM.

For some (hopefully) helpful tips, please see the Reference_ section.

Modules
-------

autoconvert
-----------
Autoconvert provides a framework for automatically converting between file formats.

*txm_to_hdf5* Traverses a search directory to find Zeiss TXM-formatted tomography data
and converts those to HDF5.

Reference
---------
Operations in the following list may depend on installation-specific values. Anywhere in
the following list that these occur, including in code snippets, the target value should
replace the variable name.

``DRAGONFLY_HOME = "C:\Program Files\Dragonfly"``

- ``DRAGONFLY_HOME\registerDLLs.bat`` ORS has provided a script that can be used by
  modules to register the DLLs required and use Dragonfly's functionality::

   import os, sys
   orsProgramData = os.path.join(os.environ['ProgramData'], 'ORS', 'Dragonfly30', 'python')
   sys.path.append(orsProgramData)
   sys.path.append(DRAGONFLY_HOME)
   os.system('registerDLLs.bat')

