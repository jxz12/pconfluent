# power-confluent drawing

![image](teaser.png)

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
where the function
```python3
draw_confluent(I, J, w_intersect=10, w_difference=1, nodesplit=True, split_length=.5, filepath=None)
```
takes `I` and `J` as edge indices, `w_intersect` and `w_difference` as weights for the greedy power graph construction algorithm, `nodesplit` and `split_length` to choose if/how nodes should be split to remove crossings, and `filepath` as the destination for the output .svg file.

The power graph construction algorithm is written in C++ for speed, while the power-to-routing graph conversion and drawing is in Python.
Splines are rendered in .svg format by using the Böhm algorithm to glue together quadratic Bézier curves (a good explanation can be found [here](https://www.semanticscholar.org/paper/An-Introduction-to-B-Spline-Curves-Sederberg/4ab68a5eac3829db3020b1f44f58b939e5ffac47)).
