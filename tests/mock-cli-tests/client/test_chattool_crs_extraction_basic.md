# CRS extraction boundary and ChatStyle compatibility

## Initial environment

Install ChatTool with ChatStyle 0.2.x. Use the Click runner, mock-only command
dispatch tests and a temporary ChatArch home. Do not call CRS, OAuth or model
services, and do not read or change user credentials.

## Expected behavior

1. Root help and the registered tree no longer advertise `crs`.
   `chattool crs --help` fails as an unknown command.
2. The parent config provider and compatibility config exports no longer define
   CRSConfig. Standalone ChatCRS owns that schema when installed.
3. The CRS implementation and config modules are absent from the source and
   built wheel. Optional `crs` and aggregate `arch` extras install bounded ChatCRS.
4. Existing non-CRS commands and the ChatStyle adapter remain callable with the
   same argument/interactive conventions. The generic OAuth service helper lives
   under `chattool.serve` and keeps its existing tests and behavior.
5. Package metadata accepts ChatStyle 0.2.x while rejecting the next minor; no
   ChatStyle runtime implementation or user configuration is changed.

```sh
python -m pytest -q tests/mock-cli-tests/client/test_chattool_crs_extraction_basic.py
python -m pytest -q tests/mock-cli-tests/chatstyle tests/code-tests/serve
```
