# power-confluent drawing
A package for drawing confluent drawings by leveraging power graph decomposition [<https://arxiv.org/abs/1810.09948>]

The package may be installed using
```pip install pconfluent```

and an example use case looks like
```python3
from pconfluent import draw_confluent
I = [0,0,0,1,1,1,2,2,2]
J = [3,4,5,3,4,5,3,4,5]
draw_confluent(I, J, filepath='K33.svg')
```

The power graph construction algorithm is written in C++ for speed, while the power-to-routing graph conversion and drawing is in Python.
Splines are rendered in .svg format by using the Boehm method to glue together quadratic Bezier curves (explanation can be found in the included .pdf file, uploaded here for convenience).
