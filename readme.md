[![Actions Status](https://github.com/adam-douglass/draughts/workflows/pytest/badge.svg)](https://github.com/adam-douglass/draughts/actions)
[![codecov](https://codecov.io/gh/adam-douglass/draughts/branch/master/graph/badge.svg?token=vQRgcsWXoq)](https://codecov.io/gh/adam-douglass/draughts)

Draughts
========

Incoming requests, outgoing queries, and messages being passed around often contain 
data that needs be normalized to account for things like missing data, types, 
or default values. This is a simple tool for generating boilerplate for data objects. 

Notes:
 - Trys to be inplace, the dict you start with should still exist with the structure+type corrections applied.
 - Let IDEs check type annotations and attribute spelling.
 - Let you annotate fields with metadata that other systems may need in order to process the document properly.
 - Properties and methods are copied in.

 
