#include <vector>
#include <unordered_set>
#include <iostream>

using std::vector;
using std::unordered_set;

struct module
{
    int idx;

    // TODO: check if these are faster with vectors instead
    //       may also be better to not use a root module
    unordered_set<module*> neighbours;
    unordered_set<module*> children;
    module(int idx) : idx(idx), neighbours(), children() {}
};

module* init_modules_undirected(int n, int m, int* I, int* J)
{
    // used to make graph undirected, in case it is not already
    vector<unordered_set<int>> undirected(n);

    vector<module*> leaves;
    leaves.reserve(n);
    for (int i=0; i<n; i++)
    {
        leaves.push_back(new module(i));
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
            leaves[i]->neighbours.insert(leaves[j]);
            leaves[j]->neighbours.insert(leaves[i]);
        }
    }
    module* root = new module(-1);
    for (int i=0; i<n; i++)
    {
        root->children.insert(leaves[i]);
    }
    return root;
}

void print_dfs(module* parent)
{
    std::cout << parent->idx << ": ";
    for (auto neighbour : parent->neighbours)
    {
        std::cout << neighbour->idx << " ";
    }
    std::cout << std::endl;

    for (auto child : parent->children)
    {
        print_dfs(child);
    }
}

// almost exactly the same function as in the Dwyer paper,
// except it simply returns the intersection
int nedges(const unordered_set<module*>& Nm, const unordered_set<module*>& Nn)
{
    int num_intersect = 0;
    for (auto nm : Nm)
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
void pgd(module* root)
{
    int new_module_idx = root->children.size(); // assumes a dense indexing
    while (true)
    {
        // find best merge
        // TODO: store these in memory to reduce computation
        int best_reduction = 0;
        module* best1;
        module* best2;
        for (auto child1 : root->children)
        {
            for (auto child2 : root->children)
            {
                if (child1->idx >= child2->idx) // don't do the same pair redundantly
                    continue;

                int reduction = nedges(child1, child2);
                std::cout << child1->idx << " " << child2->idx << " " << reduction << std::endl;
                
                if (reduction > best_reduction)
                {
                    best_reduction = reduction;
                    best1 = child1;
                    best2 = child2;
                }
            }
        }
        if (best_reduction == 0)
            break;

        // check for merge types
        bool merge1 = (best1->children.size()!=0) && (best1->neighbours.size()==best_reduction);
        bool merge2 = (best2->children.size()!=0) && (best2->neighbours.size()==best_reduction);

        // TODO: only iterate through the smaller sets in the following for loops
        if (merge1 && merge2) // full merge
        {
            // both neighbour sets are the same
            // therefore just delete one of them, the other adopting their children
            for (auto child : best2->children)
            {
                best1->children.insert(child);
            }
            root->children.erase(best2);
            delete best2;
        }
        else if (merge1)
        {
            // best1 will be left with no neighbours, and so is identical to the new parent
            // therefore remove all shared edges in 2, then parent 2 to 1
            for (auto neighbour : best1->neighbours)
            {
                best2->neighbours.erase(neighbour);
            }
            best1->children.insert(best2);
            root->children.erase(best2);
        }
        else if (merge2)
        {
            // best2 will be left with no neighbours, and so is identical to the new parent
            // therefore remove all shared edges in 1, then parent 1 to 2
            for (auto neighbour : best2->neighbours)
            {
                best1->neighbours.erase(neighbour);
            }
            best2->children.insert(best1);
            root->children.erase(best1);
        }
        else // new module
        {
            // create new module and move all shared edges to it, parent both to new
            module* new_parent = new module(new_module_idx++); // all new indices are >n
            for (auto neighbour : best1->neighbours)
            {
                if (best2->neighbours.find(neighbour) != best2->neighbours.end())
                {
                    // move all shared edges to new module
                    neighbour->neighbours.erase(best1);
                    neighbour->neighbours.erase(best2);
                    neighbour->neighbours.insert(new_parent);
                    new_parent->neighbours.insert(neighbour);
                }
            }
            for (auto neighbour : new_parent->neighbours)
            {
                // remove from originals
                best1->neighbours.erase(neighbour);
                best2->neighbours.erase(neighbour);
            }
            // parent to new
            new_parent->children.insert(best1);
            new_parent->children.insert(best2);
            root->children.insert(new_parent);
            root->children.erase(best1);
            root->children.erase(best2);
        }
    }
}

// void routing(module* root);
// returns:
// n, I, J, I2, J2
// indices of tree edges, indices of power edges
