Draughts
========

_Type checking data models; you might call them checkers_

This module is a utility I've ended up writing multiple times for different 
projects to perform type and structure checking for input/output documents.

When receiving a dictionary of data as part of an API or database query it would be 
nice to be sure all fields are present and of the right type, defaults are set, etc.

Ideally this should be:   
 - Reasonably fast for type checking in pure python.
 - Inplace, the dict you start with should still exist with the type corrections applied.
 - Lets IDEs check type annotations and attribute spelling.
 - Extensible so that constraints can be pushed into the model as much as possible.
 - Let you annotate fields with metadata that other systems may need in order to process the document properly.
 
 
