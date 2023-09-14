# Changelog

## 0.5.1 - September 15, 2023

### ✨ Improved

* Several hotfixes, some quite hacky, to speed up requests to the WAGO module and the pressure transducers, and to better deal with failures. Connection and request timeouts have been increased and in some cases the code will retry several times if there's an error.
* Bumped `drift` to 1.1.0.

### ⚙️ Engineering

* Lint using `ruff`.


## 0.5.0 - July 10, 2023

### ✨ Improved

* Bump `CLU` to 2.1.0.
* Do not make `SPECTRO` required if only one controller is present.
* Various Docker image and build modifications for deployment in Kubernetes.


## 0.4.0 - May 28, 2022

### 💥 Breaking changes

* [#65](https://github.com/sdss/lvmieb/pull/65) Major refactor of `lmvieb`. Most actor commands have kept the same syntax but this version is generally a breaking change with respect to 0.3.0. The main changes are:

  * Split IEBController into several classes for motors, WAGO, pressure transducers, and depth probes. In the previos code the `IebController` handled everything but actually multiple instances are generated for each spectrograph, one for each type of device. In this version the `IEBController` is a simple collection of individual controllers.
  * Simplified a bit how the actor is instantiated from the configuration file to take advantage of the new `IEBController`.
  * Done some refactoring of the actor commands but for the most part the command names and options are the same.
  * Added a keyword schema and some general engineering tweaks.
  * Improvements to testing, docs building, etc.
