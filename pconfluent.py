import pgd as cpp
import numpy as np

class routing_node:
    def __init__(self, idx):
        self.idx = idx
        self.parent = None
        self.children = []
        self.pout = []
        self.pin = []
        #self.split = False
        
def reconstruct_routing(Ir, Jr, Ip, Jp, nodesplit=False):
    """reconstructs the hierarchy of routing nodes from the edges."""
    rnodes = {}
    for ij in range(len(Ir)):
        i = Ir[ij]
        j = Jr[ij]
        if i not in rnodes.keys():
            rnodes[i] = routing_node(i)
        if j not in rnodes.keys():
            rnodes[j] = routing_node(j)

        rnodes[i].children.append(rnodes[j])
        # TODO: this may not be necessary when generalising to strict-confluent
        if rnodes[j].parent is not None:
            raise "node has more than one parent"
        rnodes[j].parent = rnodes[i]

    # add power edges
    for ij in range(len(Ip)):
        i = Ip[ij]
        j = Jp[ij]
        if i not in rnodes.keys():
            rnodes[i] = routing_node(i)
        if j not in rnodes.keys():
            rnodes[j] = routing_node(j)

        rnodes[i].pout.append(rnodes[j])
        rnodes[j].pin.append(rnodes[i])

    # split crossing-artifact nodes
    # TODO: make the split edge shorter?
    if nodesplit:
        new_idx = len(rnodes)
        splitnodes = []
        for node in rnodes.values():
            if len(node.children)>=2 and ((1 if node.parent is not None else 0)+len(node.pout)+len(node.pin))>=2:
                splitnode = routing_node(new_idx)
                #splitnode.split = True

                splitnode.children = node.children
                for child in splitnode.children:
                    child.parent = splitnode

                splitnode.parent = node
                node.children = [splitnode]

                splitnodes.append(splitnode)
                new_idx += 1

        for splitnode in splitnodes:
            rnodes[splitnode.idx] = splitnode

    return rnodes

def get_routing_adjacency(rnodes):
    I = []
    J = []
    # V = []
    for node in rnodes.values():
        for child in node.children:
            I.append(node.idx)
            J.append(child.idx)
            #if child.split:
            #    V.append(.5)
            #else:
            #    V.append(1)
        for pout in node.pout:
            I.append(node.idx)
            J.append(pout.idx)
            #V.append(1)

    return I,J#,V

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
    for node in rnodes.values():
        for adjacent in node.pout:
            paths_to = []
            init_paths_to_leaves(node, [], paths_to)
            finish_paths_from_leaves(adjacent, [], paths_to, all_paths)

    return all_paths


def draw_bspline_quad(layout, path):
    m = len(path)
    if m < 2:
        raise "path is less than 2 points long"
    if m == 2:
        p0 = layout[path[0]]
        p1 = layout[path[1]]
        print('<path d="M {} {} L {} {}"/>'.format(p0[0],p0[1],p1[0],p1[1]))
    else:
        nseg = m - 2
        p00 = layout[path[0]]
        p01 = layout[path[1]]
        print('<path d="M {} {} Q {} {}'.format(p00[0],p00[1],p01[0],p01[1]), end='')

        for i in range(1, nseg):
            p11 = .5*layout[path[i]] + .5*layout[path[i+1]]
            print(' {} {} T'.format(p11[0], p11[1]), end='')
            
        p22 = layout[path[-1]]
        print(' {} {}"/>'.format(p22[0],p22[1]))
    #else:
    #    p01 = layout[path[0]]
    #    p12 = layout[path[1]]
    #    p11 = .5*p01 + .5*p12
    #    print('<path d="M {} {} L {} {} Q {} {}'.format(p01[0], p01[1], p11[0], p11[1], p12[0], p12[1]), end='')

    #    for i in range(1, len(path)-2):
    #        p22 = .5*layout[path[i]] + .5*layout[path[i+1]]
    #        print(' {} {} T'.format(p22[0], p22[1]), end='')

    #    p33 = .5*layout[path[-2]] + .5*layout[path[-1]]
    #    end = layout[path[-1]]
    #    print(' {} {} L {} {}"/>'.format(p33[0], p33[1], end[0], end[1]))

def draw_bspline_cubic(layout, path):
    m = len(path)
    if m < 2:
        raise "path is less than 2 points long"
    if m == 2:
        p0 = layout[path[0]]
        p1 = layout[path[1]]
        print('<path d="M {} {} L {} {}"/>'.format(p0[0],p0[1],p1[0],p1[1]))
    else:
        p000 = layout[path[0]] # not strictly correct, but works
        p112 = 2/3*layout[path[0]] + 1/3*layout[path[1]]
        p122 = 1/3*layout[path[0]] + 2/3*layout[path[1]]
        print('<path d="M {} {} C {} {} {} {}'.format(p000[0],p000[1],p112[0],p112[1],p122[0],p122[1]), end='')

        for i in range(1, len(path)-1):
            p123 = layout[path[i]]
            p234 = layout[path[i+1]]
            p223 = 2/3*p123 + 1/3*p234
            p233 = 1/3*p123 + 2/3*p234
            p222 = .5*p122 + .5*p223

            print(' {} {} S {} {}'.format(p222[0], p222[1], p233[0], p233[1]), end='')
            p122 = p233

        end = layout[path[-1]]
        print(' {} {}"/>'.format(end[0], end[1]))

    #elif m == 3:
    #    p000 = layout[path[0]]
    #    # p001 = 1/3*layout[path[0]] + 2/3*layout[path[1]]
    #    # p011 = 2/3*layout[path[1]] + 1/3*layout[path[2]]
    #    p001 = 1/2*layout[path[0]] + 1/2*layout[path[1]]
    #    p011 = 1/2*layout[path[1]] + 1/2*layout[path[2]]
    #    p111 = layout[path[2]]
    #    print('<path d="M {} {} C {} {} {} {} {} {}"/>'.format(p000[0],p000[1],p001[0],p001[1],p011[0],p011[1],p111[0],p111[1]))
    #elif m == 4:
    #    p000 = layout[path[0]]
    #    p001 = layout[path[1]]
    #    p011 = layout[path[2]]
    #    p111 = layout[path[3]]
    #    print('<path d="M {} {} C {} {} {} {} {} {}"/>'.format(p000[0],p000[1],p001[0],p001[1],p011[0],p011[1],p111[0],p111[1]))
    #else:
    #    nseg = m - 3
    #    p000 = layout[path[0]]
    #    p001 = layout[path[1]]
    #    p011 = .5*layout[path[1]] + .5*layout[path[2]]
    #    print('<path d="M {} {} C {} {} {} {}'.format(p000[0],p000[1],p001[0],p001[1],p011[0],p011[1]), end='')

    #    for i in range(2, nseg):
    #        p112 = .75*layout[path[i]] + .25*layout[path[i+1]] # symmetric about the knot
    #        p111 = .5*p011 + .5*p112 # knot
    #        p122 = .25*layout[path[i]] + .75*layout[path[i+1]]
    #        print(' {} {} S {} {}'.format(p111[0],p111[1],p122[0],p122[1]), end='')
    #        p011 = p122
    #        
    #    p112 = .5*layout[path[-3]] + .5*layout[path[-2]]
    #    p111 = .5*p011 + .5*p112
    #    p122 = layout[path[-2]]
    #    p222 = layout[path[-1]]
    #    print(' {} {} S {} {} {} {}"/>'.format(p111[0],p111[1],p122[0],p122[1],p222[0],p222[1]))

# TODO: change number of significant figures for coordinates
def draw_svg(rnodes, paths, layout, noderadius=.2, linkwidth=.05, width=750, border=50, linkopacity=1):
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
            
    print('<svg width="{}" height="{}" xmlns="http://www.w3.org/2000/svg">'.format(width, width))
    print('<style type="text/css">')
    print('path{{stroke:black;stroke-width:{};stroke-opacity:{};stroke-linecap:round;fill:transparent}}'.format(scale*linkwidth,linkopacity))
    print('circle{{r:{}}}'.format(scale*noderadius))
    print('</style>');

    # draw splines
    for path in paths:
        draw_bspline_quad(X_svg, path)
        #draw_bspline_cubic(X_svg, path)
    # draw nodes
    for node in rnodes.values():
        if len(node.children) == 0:
            print('<circle cx="{}" cy="{}"/>'.format(X_svg[node.idx][0],X_svg[node.idx][1]))
        #else:
        #    print('<circle cx="{}" cy="{}" fill="red" fill-opacity=".5"/>'.format(X_svg[node.idx][0],X_svg[node.idx][1]))

    print('</svg>')
    

# I = [0,0,0, 1,1,1, 2,2,2]
# J = [3,4,5, 3,4,5, 3,4,5]
# Ir, Jr, Ip, Jp = cpp.routing(6, I, J)

Ir = [6,6,6, 7,7, 8,8]
Jr = [0,1,2, 3,8, 4,5]
Ip = [6,9]
Jp = [7,8]

# Ir = []
# Jr = []
# Ip = [0,0,0, 1,1,1, 2,2,2, 6,6]
# Jp = [3,4,5, 3,4,5, 3,4,5, 3,4]

rnodes = reconstruct_routing(Ir, Jr, Ip, Jp, nodesplit=False)

import s_gd2
I,J = get_routing_adjacency(rnodes)
layout = s_gd2.layout(len(rnodes), I, J)

paths = find_spline_paths(rnodes)
draw_svg(rnodes, paths, layout)
