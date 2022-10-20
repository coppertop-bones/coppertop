Naming is important

But not as hard as people make out.

No matter how plastic the language, and even if we have access to all the affected source code, changing names has 
an impact, cost of transition in the code base and cost of transition in people's minds. We should, therefore, choose 
them as if they are set in stone and can never be changed.

In general function names should be pleasing although sometimes they can't.

criteria
1) fits into the library's culture
2) pithy - short is good, expressive is good
3) clear - tacit is better than explicit is better than implicit

Goal is to be able to predict from the names and inferred argument types (including that implied by the name) what
a function does with a 95% success rate.


unbreakable rules in dm
1) type should not change because of cardinality - I find this to be the biggest (1-2 orders of magnitude) source
of bugs when using numpy.


namespace location

By default functions live in root - these are the easiest to use and mean less imports to maintain. Sometimes
a function would need a parameter to select which has no value other than to force the user to select which one to use. 
Algorithms are typical examples - e.g. np.leastsq in the past has been different to scipy.leastsq. Rather than
pass in a function selection parameter we use the name space as it leads to clearer code.

E.g. dm.linalg.np.leastsq, dm.linalg.scipy.leastsq, dm.linalg.mkl.leastsq, dm.linalg.nag.leastsq

All these could have identical function signatures.

type / data conversions are a notable exception- it is considered that passing in a selection parameter is much
clearer than selecting via name or namespace.
