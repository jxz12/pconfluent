import pgd as cpp
import numpy as np
import s_gd2

class routing_node:
    def __init__(self, idx):
        self.idx = idx
        self.parent = None
        self.children = []
        self.pout = []
        self.pin = []
        
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
            raise "node has more than one parent"
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

                rnodes.append(splitnode)

    return rnodes

# TODO: perhaps make split edges shorter
def get_routing_adjacency(rnodes):
    I = []
    J = []
    for node in rnodes:
        for child in node.children:
            I.append(node.idx)
            J.append(child.idx)
        for pout in node.pout:
            I.append(node.idx)
            J.append(pout.idx)

    return I,J

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

def draw_bspline_quad(layout, path):
    """draws a quadratic b-spline, with an open knot vector but no repeated control points"""
    svg = []
    m = len(path)
    if m < 2:
        raise "path is less than 2 points long"
    if m == 2:
        p0 = layout[path[0]]
        p1 = layout[path[1]]
        svg.append('<path d="M {} {} L {} {}"/>'.format(p0[0],p0[1],p1[0],p1[1]))
    else:
        nseg = m - 2
        p00 = layout[path[0]]
        p01 = layout[path[1]]
        svg.append('<path d="M {} {} Q {} {}'.format(p00[0],p00[1],p01[0],p01[1]))

        for i in range(1, nseg):
            p11 = .5*layout[path[i]] + .5*layout[path[i+1]]
            svg.append(' {} {} T'.format(p11[0], p11[1]))
            
        p22 = layout[path[-1]]
        svg.append(' {} {}"/>'.format(p22[0],p22[1]))

    return(''.join(svg))

def draw_bspline_cubic(layout, path):
    """draws a cubic b-spline, with an open knot vector and repeated control points"""
    svg = []
    m = len(path)
    if m < 2:
        raise "path is less than 2 points long"
    if m == 2:
        p0 = layout[path[0]]
        p1 = layout[path[1]]
        svg.append('<path d="M {} {} L {} {}"/>'.format(p0[0],p0[1],p1[0],p1[1]))
    else:
        p000 = layout[path[0]] # not strictly correct, but works
        p112 = 2/3*layout[path[0]] + 1/3*layout[path[1]]
        p122 = 1/3*layout[path[0]] + 2/3*layout[path[1]]
        svg.append('<path d="M {} {} C {} {} {} {}'.format(p000[0],p000[1],p112[0],p112[1],p122[0],p122[1]))

        for i in range(1, len(path)-1):
            p123 = layout[path[i]]
            p234 = layout[path[i+1]]
            p223 = 2/3*p123 + 1/3*p234
            p233 = 1/3*p123 + 2/3*p234
            p222 = .5*p122 + .5*p223

            svg.append(' {} {} S {} {}'.format(p222[0], p222[1], p233[0], p233[1]))
            p122 = p233

        end = layout[path[-1]]
        svg.append(' {} {}"/>'.format(end[0], end[1]))

    return(''.join(svg))

# TODO: change number of significant figures for coordinates
def draw_svg(rnodes, paths, layout, filepath=None,
             noderadius=.2, linkwidth=.05, width=750, border=50, linkopacity=1):
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
    svg.append('<svg width="{}" height="{}" xmlns="http://www.w3.org/2000/svg">'.format(width, width))
    svg.append('<style type="text/css">')
    svg.append('path{{stroke:black;stroke-width:{};stroke-opacity:{};stroke-linecap:round;fill:transparent}}'.format(scale*linkwidth,linkopacity))
    svg.append('circle{{r:{}}}'.format(scale*noderadius))
    svg.append('</style>');

    # draw splines
    for path in paths:
        svg.append(draw_bspline_quad(X_svg, path))

    # draw only leaf nodes
    for node in rnodes:
        if len(node.children) == 0:
            svg.append('<circle cx="{}" cy="{}"/>'.format(X_svg[node.idx][0],X_svg[node.idx][1]))

    svg.append('</svg>')

    if filepath is None or filepath == '':
        print('\n'.join(svg))
    else:
        with open(filepath, 'w') as f:
            f.write('\n'.join(svg))
    
def draw_confluent(I, J, edge_weight=1, module_weight=1, crossing_weight=1, nodesplit=True, filepath=None):
    n = max(max(I), max(J)) + 1
    Ir, Jr, Ip, Jp = cpp.routing_swig(n, I, J, edge_weight, module_weight, crossing_weight)

    rnodes = reconstruct_routing(Ir, Jr, Ip, Jp, nodesplit=nodesplit)
    paths = find_spline_paths(rnodes)

    I,J = get_routing_adjacency(rnodes)
    layout = s_gd2.layout(len(rnodes), I, J)

    draw_svg(rnodes, paths, layout, filepath)

if __name__ == "__main__":
    #I = [0,0,0, 1,1,1, 2,2,2, 6,6]
    #J = [3,4,5, 3,4,5, 3,4,5, 4,5]
    I = [0,0,0,0, 1,1,1, 2,2, 3,3,3, 4,4,4, 5]
    J = [1,2,3,4, 2,6,7, 6,7, 4,6,7, 5,6,7, 6]
    draw_confluent(I, J, filepath='test.svg')
