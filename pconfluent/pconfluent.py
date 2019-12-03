from .swig import pgd as cpp
import numpy as np
import s_gd2
__all__ = ['find_power_graph', 'draw_confluent']

class routing_node:
    def __init__(self, idx):
        self.idx = idx
        self.parent = None
        self.children = []
        self.pout = []
        self.pin = []
        self.split = False
        
def reconstruct_routing(Ir, Jr, Ip, Jp, nodesplit=False):
    """reconstructs the hierarchy of routing nodes from its edges."""
    rnodes = []
    n = max(max(Ir), max(Jr), max(Ip), max(Jp)) + 1 # assume contiguous indices
    for i in range(n):
        rnodes.append(routing_node(i))

    # add routing edges
    for ij in range(len(Ir)):
        i = Ir[ij]
        j = Jr[ij]
        rnodes[i].children.append(rnodes[j])
        if rnodes[j].parent is not None:
            raise ValueError("node has more than one parent")
        rnodes[j].parent = rnodes[i]

    # add power edges
    for ij in range(len(Ip)):
        i = Ip[ij]
        j = Jp[ij]
        rnodes[i].pout.append(rnodes[j])
        rnodes[j].pin.append(rnodes[i])

    # split 'crossing-artifact' nodes
    if nodesplit:
        for i in range(len(rnodes)):
            node = rnodes[i]
            outgoing = len(node.children)
            incoming = (1 if node.parent is not None else 0)+len(node.pout)+len(node.pin)
            if incoming>=2 and outgoing>=2:

                splitnode = routing_node(len(rnodes))

                splitnode.children = node.children
                for child in splitnode.children:
                    child.parent = splitnode

                splitnode.parent = node
                node.children = [splitnode]

                splitnode.split = True
                #node.split = True

                rnodes.append(splitnode)

    return rnodes

def get_routing_adjacency(rnodes, split_length=1):
    I = []
    J = []
    V = []
    for node in rnodes:
        for child in node.children:
            I.append(node.idx)
            J.append(child.idx)
            V.append(split_length if child.split else 1)
        for pout in node.pout:
            I.append(node.idx)
            J.append(pout.idx)
            V.append(1)

    return I,J,V

# DFS to init paths to one end
def init_paths_to_leaves(node, stack, paths):
    stack.append(node.idx)
    if len(node.children) == 0:
        # if leaf, create path
        paths.append([i for i in stack])
    else:
        for child in node.children:
            init_paths_to_leaves(child, stack, paths)
    stack.pop()

# DFS to finish paths from other end
def finish_paths_from_leaves(node, stack, paths_to, all_paths):
    stack.append(node.idx)
    if len(node.children) == 0:
        # if leaf, finish path
        path_from = [i for i in reversed(stack)]
        for path_to in paths_to:
            all_paths.append(path_from + path_to)
    else:
        for child in node.children:
            finish_paths_from_leaves(child, stack, paths_to, all_paths)
    stack.pop()

def find_spline_paths(rnodes):
    all_paths = []
    for node in rnodes:
        for adjacent in node.pout:
            paths_to = []
            init_paths_to_leaves(node, [], paths_to)
            finish_paths_from_leaves(adjacent, [], paths_to, all_paths)

    return all_paths

def draw_bspline_quadratic(layout, path):
    """draws a quadratic b-spline, with an open knot vector but no repeated control points"""
    svg = []
    m = len(path)
    if m < 2:
        raise ValueError("path is less than 2 points long")
    if m == 2:
        p0 = layout[path[0]]
        p1 = layout[path[1]]
        svg.append('<path d="M {:.1f} {:.1f} L {:.1f} {:.1f}"/>'.format(p0[0],p0[1],p1[0],p1[1]))
    else:
        nseg = m - 2
        p00 = layout[path[0]]
        p01 = layout[path[1]]
        svg.append('<path d="M {:.1f} {:.1f} Q {:.1f} {:.1f}'.format(p00[0],p00[1],p01[0],p01[1]))

        for i in range(1, nseg):
            p11 = .5*layout[path[i]] + .5*layout[path[i+1]]
            svg.append(' {:.1f} {:.1f} T'.format(p11[0], p11[1]))
            
        p22 = layout[path[-1]]
        svg.append(' {:.1f} {:.1f}"/>'.format(p22[0],p22[1]))

    return(''.join(svg))

def draw_bspline_cubic(layout, path):
    """draws a cubic b-spline, with an open knot vector and repeated control points"""
    svg = []
    m = len(path)
    if m < 2:
        raise ValueError("path is less than 2 points long")
    if m == 2:
        p0 = layout[path[0]]
        p1 = layout[path[1]]
        svg.append('<path d="M {:.1f} {:.1f} L {:.1f} {:.1f}"/>'.format(p0[0],p0[1],p1[0],p1[1]))
    else:
        p000 = layout[path[0]] # not strictly correct, but works
        p112 = 2/3*layout[path[0]] + 1/3*layout[path[1]]
        p122 = 1/3*layout[path[0]] + 2/3*layout[path[1]]
        svg.append('<path d="M {:.1f} {:.1f} C {:.1f} {:.1f} {:.1f} {:.1f}'.format(p000[0],p000[1],p112[0],p112[1],p122[0],p122[1]))

        for i in range(1, len(path)-1):
            p123 = layout[path[i]]
            p234 = layout[path[i+1]]
            p223 = 2/3*p123 + 1/3*p234
            p233 = 1/3*p123 + 2/3*p234
            p222 = .5*p122 + .5*p223

            svg.append(' {:.1f} {:.1f} S {:.1f} {:.1f}'.format(p222[0], p222[1], p233[0], p233[1]))
            p122 = p233

        end = layout[path[-1]]
        svg.append(' {:.1f} {:.1f}"/>'.format(end[0], end[1]))

    return(''.join(svg))


def draw_svg(rnodes, paths, layout, filepath=None,
             noderadius=.2, linkwidth=.05, width=750, border=50, nodeopacity=1, linkopacity=1):
    X = layout
    n = len(X)
    X_min = [min(X[i,0] for i in range(n)), min(X[i,1] for i in range(n))]
    X_max = [max(X[i,0] for i in range(n)), max(X[i,1] for i in range(n))]

    range_max = max(X_max[0]-X_min[0], X_max[1]-X_min[1]) # taller or wider
    range_max += 2*noderadius # guarantee no nodes are cut off at the edges
    scale = (width-2*border) / range_max

    X_svg = np.empty((n,2))
    for i in range(n):
        X_svg[i] = (X[i] - X_min) * scale
        X_svg[i] += [border + scale*noderadius, border + scale*noderadius]
            
    svg = []
    svg.append('<svg width="{:.0f}" height="{:.0f}" xmlns="http://www.w3.org/2000/svg">'.format(width, width))
    svg.append('<style type="text/css">')
    svg.append('path{{stroke:black;stroke-width:{:.3f};stroke-opacity:{:.3f};stroke-linecap:round;fill:transparent}}'.format(scale*linkwidth,linkopacity))
    svg.append('circle{{r:{:.3f};fill:black;fill-opacity:{:.3f}}}'.format(scale*noderadius,nodeopacity))
    svg.append('</style>')

    # draw splines
    for path in paths:
        svg.append(draw_bspline_quadratic(X_svg, path))
        #svg.append(draw_bspline_cubic(X_svg, path))

    for node in rnodes:
        # draw only leaf nodes
        if len(node.children) == 0:
            svg.append('<circle cx="{:.1f}" cy="{:.1f}"/>'.format(X_svg[node.idx][0],X_svg[node.idx][1]))
        #else:
        #    svg.append('<circle cx="{}" cy="{}" fill="red" opacity=".5"/>'.format(X_svg[node.idx][0],X_svg[node.idx][1]))

    svg.append('</svg>')

    if filepath is None or filepath == '':
        print('\n'.join(svg))
    else:
        with open(filepath, 'w') as f:
            f.write('\n'.join(svg))
    
def find_power_graph(I, J, w_intersect=10, w_difference=1):
    """takes a graph with edges I,J, and returns a power
    graph with routing edges Ir,Jr and power edges Ip,Jp.
    Note that this treats the graph as undirected, and will
    internally convert edges to be undirected if not already."""
    n = int(max(max(I), max(J)) + 1)
    Ir, Jr, Ip, Jp = cpp.routing_swig(n, I, J, w_intersect, w_difference)
    return Ir, Jr, Ip, Jp

def draw_confluent(Ir, Jr, Ip, Jp, nodesplit=True, split_length=.5, filepath=None):
    """takes a power graph with routing edges Ir,Jr and
    power edges Ip,Jp and draws the corresponding power-confluent
    drawing, using quadratic bezier splines to thread through the
    routing graph. The graph layout is performed by stochastic
    gradient descent, and the drawing is rendered in .svg format."""
    rnodes = reconstruct_routing(Ir, Jr, Ip, Jp, nodesplit=nodesplit)
    paths = find_spline_paths(rnodes)

    I,J,V = get_routing_adjacency(rnodes, split_length=split_length)
    layout = s_gd2.layout(I, J, V)

    draw_svg(rnodes, paths, layout, filepath)

    #print('{} {}'.format(n,len(I)))
    #print('power edges: {}'.format(len(Ip)))
    #print('power groups: {}'.format(max(max(Ir),max(Jr))+1-n))

