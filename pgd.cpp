#include <vector>
#include <unordered_set>
#include <iostream>

struct module
{
    int idx;
    std::unordered_set<int> neighbours;
    std::vector<module*> children; // can never lose children, so removal is not a problem
    // TODO: check if should be a hashset instead
    module(int idx) : idx(idx), neighbours(), children() {}
};

module* init_modules_undirected(int n, int m, int* I, int* J)
{
    // used to make graph undirected, in case it is not already
    std::vector<std::unordered_set<int>> undirected(n);

    module* super = new module(-1);
    super->children.reserve(n);
    for (int i=0; i<n; i++)
    {
        super->children.push_back(new module(i));
    }

    for (int ij=0; ij<m; ij++)
    {
        int i = I[ij], j = J[ij];
        if (i >= n || j >= n)
            throw "i or j bigger than n";

        if (undirected[j].find(i) == undirected[j].end()) // if edge not seen
        {
            undirected[i].insert(j);
            undirected[j].insert(i);
            super->children[i]->neighbours.insert(j);
            super->children[j]->neighbours.insert(i);
        }
    }
    return super;
}

void print_dfs(module* parent)
{
    std::cout << parent->idx << ": ";
    for (int neighbour : parent->neighbours)
    {
        std::cout << neighbour << " ";
    }
    std::cout << std::endl;

    for (module* child : parent->children)
    {
        print_dfs(child);
    }
}

// almost exactly the same function as in the Dwyer paper,
// except it simply returns the intersection
int nedges(const std::unordered_set<int>& Nm, const std::unordered_set<int>& Nn)
{
    int num_intersect = 0;
    for (int nm : Nm)
    {
        if (Nn.find(nm) != Nn.end())
        {
            num_intersect += 1;
        }
    }
    return num_intersect;
}
// make it take modules as input, and
// always iterate through the smaller set for better complexity
int nedges(const module* m, const module* n)
{
    if (m->neighbours.size() > n->neighbours.size())
    {
        return nedges(m->neighbours, n->neighbours);
    }
    else
    {
        return nedges(n->neighbours, m->neighbours);
    }
}
/*
void pgd(module* super)
{
    int new_module_idx = -2;
    while (true)
    {
        // find best merge
        int best_reduction = 0;
        module* best1;
        module* best2;
        for (module* child1 : super->children)
        {
            for (module* child2 : super->children)
            {
                if (child1->idx >= child2->idx) // don't do the same pair redundantly
                    continue;

                int reduction = nedges(child1, child2);
                std::cout << child1->idx << " " << child2->idx << " " << reduction << std::endl;
                
                if (reduction > best_reduction)
                {
                    best1 = child1;
                    best2 = child2;
                }
            }
        }
        if (best_reduction == 0)
            break;

        // check for full merges
        bool merge1 = (best1->children.size()!=0) && (best1->neighbours.size()==best_reduction);
        bool merge2 = (best2->children.size()!=0) && (best2->neighbours.size()==best_reduction);

        // do a full merge
        if (merge1 && merge2)
        {
            // move all 2's edges into 1, then remove 2
        }
        else if (merge1)
        {
            // move all 2's shared edges into 1, then parent 1 to 2
        }
        else if (merge2)
        {
            // move all 1's shared edges into 2, then parent 2 to 1
        }
        else
        {
            // create new module and move all shared edges to it, parent both to new
        }
    }
}
*/
