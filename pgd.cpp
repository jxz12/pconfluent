#include <vector>
#include <unordered_set>
#include <iostream>

using std::vector;
using std::unordered_set;

struct module
{
    int idx;

    // TODO: check if these are faster with vectors instead
    unordered_set<module*> neighbours;
    unordered_set<module*> children;

    module(int idx);
    module(int n, int m, int* I, int* J, int idx=-1);
};
void delete_modules(module* root);

void pgd(module* root, int edge_score=2, int module_score=1, int crossing_score=1);

int nedges(module* m, module* n);
int nmodules(module* m, module* n, int intersect);
int ncrossings(module* m, module* n, int intersect);
void routing(const module* root, vector<int>& Ir, vector<int>& Jr, vector<int>& Ip, vector<int>& Jp);

void routing_swig(int n, int m, int* I, int* J,
                  int* len_r, int** Ir, int** Jr, int* len_p, int** Ip, int** Jp,
                  int edge_weight=2, int module_weight=1, int crossing_weight=1);


module::module(int idx) : idx(idx), neighbours(), children()
{}

// this initialises the module into a super module connected to trivial top modules
// it does not matter what idx it takes
// TODO: may be faster to use a vector rather than a root module like this
module::module(int n, int m, int* I, int* J, int idx) : idx(idx)
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

        if (undirected[j].find(i) == undirected[j].end()) // cuts out repeat edges
        {
            undirected[i].insert(j);
            undirected[j].insert(i);
            leaves[i]->neighbours.insert(leaves[j]);
            leaves[j]->neighbours.insert(leaves[i]);
        }
    }
    for (int i=0; i<n; i++)
    {
        children.insert(leaves[i]);
    }
}

void delete_modules(module* parent)
{
    for (auto child : parent->children)
    {
        delete_modules(child);
    }
    delete parent;
}

void pgd(module* root, int edge_score, int module_score, int crossing_score)
{
    int new_module_idx = root->children.size(); // assumes that indices are condensed
    while (true)
    {
        module* best1;
        module* best2;
        int best_score=0;
        // TODO: store these scores in memory to reduce computation?

        // find best merge out of all possible combinations
        for (auto child1 : root->children)
        {
            for (auto child2 : root->children)
            {
                if (child1->idx >= child2->idx) // don't do the same pair redundantly
                    continue;

                // intersection is the number of eliminated edges
                int intersect = nedges(child1, child2);
                int modules = nmodules(child1, child2, intersect);
                int crossings = ncrossings(child1, child2, intersect);

                // sum points for edges and modules
                int score = intersect*edge_score + modules*module_score + crossings*crossing_score;
                std::cerr << child1->idx << "+" << child2->idx << "=" << score << std::endl;
                
                if (score > best_score)
                {
                    best1 = child1;
                    best2 = child2;
                    best_score = score;
                }
            }
        }
        if (best_score == 0)
            break;

        std::cerr << new_module_idx << std::endl;

        // check if either module will be empty after the merge
        int best_intersect = nedges(best1, best2);
        bool empty1 = (best1->children.size()!=0) && (best1->neighbours.size()==best_intersect);
        bool empty2 = (best2->children.size()!=0) && (best2->neighbours.size()==best_intersect);
        
        // perform the merge itself
        // TODO: only iterate through the smaller sets in the following for loops
        if (empty1 && empty1) // full merge
        {
            // both neighbour sets are the same
            // therefore just delete one of them, the other adopting their children
            for (auto child : best2->children)
            {
                best1->children.insert(child);
            }
            for (auto neighbour : best2->neighbours)
            {
                // clear hanging neighbours
                neighbour->neighbours.erase(best2);
            }
            root->children.erase(best2);
            delete best2;
        }
        else if (empty1)
        {
            // best1 will be left with no neighbours, and so is identical to the new parent
            // therefore remove all shared edges in 2, then parent 2 to 1
            for (auto neighbour : best1->neighbours)
            {
                best2->neighbours.erase(neighbour);
                neighbour->neighbours.erase(best1);
                neighbour->neighbours.erase(best2);
                neighbour->neighbours.insert(best1);
            }
            best1->children.insert(best2);
            root->children.erase(best2);
        }
        else if (empty2)
        {
            // above vice versa
            for (auto neighbour : best2->neighbours)
            {
                best1->neighbours.erase(neighbour);
                neighbour->neighbours.erase(best1);
                neighbour->neighbours.erase(best2);
                neighbour->neighbours.insert(best2);
            }
            best2->children.insert(best1);
            root->children.erase(best1);
        }
        else // neither empty, so new module
        {
            // create new module and move all shared edges to it, parent both to new
            module* new_parent = new module(new_module_idx++);

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
                // remove shared from originals
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

// almost exactly the same function as in the Dwyer paper,
// except it simply returns the intersection
int nedges(unordered_set<module*>& Nm, unordered_set<module*>& Nn)
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
int nedges(module* m, module* n)
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
int nmodules(module* m, module* n, int intersect)
{
    // don't penalise when either child is a leaf, because it cannot ever be merged

    //return (m->children.size()==0 || n->children.size()==0)? 0 :
    return       (m->neighbours.size()==intersect && n->neighbours.size()==intersect)? 1 :
           (m->neighbours.size()!=intersect && n->neighbours.size()!=intersect)? -1 : 0;
}
int ncrossings(module* m, module* n, int intersect)
{
    int diff1 = m->neighbours.size() - intersect;
    int diff2 = n->neighbours.size() - intersect;

    int crossings = (m->neighbours.find(n)!=m->neighbours.end())? diff1+diff2 : diff1+diff2-2;
    return -crossings;
}

void reindex_modules(module* root, int& new_idx)
{
    if (root->children.size() != 0)
    {
        root->idx = new_idx++;
        for (auto child : root->children)
        {
            reindex_modules(child, new_idx);
        }
    }
}
void reindex_modules_contiguous(module* root, int n_leaves)
{
    for (auto top : root->children)
    {
        reindex_modules(top, n_leaves);
    }
}

void add_routing_edges(const module* parent, vector<int>& Ir, vector<int>& Jr)
{
    for (auto child : parent->children)
    {
        std::cerr << "r: " << parent->idx << " " << child->idx << std::endl;

        Ir.push_back(parent->idx);
        Jr.push_back(child->idx);
        add_routing_edges(child, Ir, Jr);
    }
}
void add_power_edges(const module* parent, vector<int>& Ip, vector<int>& Jp)
{
    for (auto neighbour : parent->neighbours)
    {
        std::cerr << "p: " << parent->idx << " " << neighbour->idx << std::endl;

        if (parent->idx < neighbour->idx) // only add edges once
        {
            Ip.push_back(parent->idx);
            Jp.push_back(neighbour->idx);
        }
    }
    for (auto child : parent->children)
    {
        add_power_edges(child, Ip, Jp);
    }
}

void routing(const module* root, vector<int>& Ir, vector<int>& Jr, vector<int>& Ip, vector<int>& Jp)
{
    for (auto top : root->children) // 'throw away' root
    {
        std::cerr << "top: " << top->idx << std::endl;
        add_routing_edges(top, Ir, Jr);
        add_power_edges(top, Ip, Jp);
    }
}

// get memory fro a
int* steal_vector_array(vector<int>& v)
{
    //*Ir = new int[*len_r];
    //std::memcpy(*Ir, Ir_vec.data(), *len_r*sizeof(int));
    int* stolen = v.data();
    new (&v) std::vector<int>; // 'placement new' to replace v with empty vector, old storage leaked
    return stolen;
}

// Ir & Jr are routing edges, Ip & Jp are power edges
// these are all output parameters
// to be used in swig
void routing_swig(int n, int m, int* I, int* J,
                  int* len_r, int** Ir, int** Jr, int* len_p, int** Ip, int** Jp,
                  int edge_weight, int module_weight, int crossing_weight)
{
    // get power graph
    module* root = new module(n, m, I, J);
    pgd(root, edge_weight, module_weight, crossing_weight);

    // condense indices
    reindex_modules_contiguous(root, n);

    // get routing graph
    vector<int> Ir_vec, Jr_vec, Ip_vec, Jp_vec;
    routing(root, Ir_vec, Jr_vec, Ip_vec, Jp_vec);

    // force a 'memory leak', so that python has access to the data
    *len_r = Ir_vec.size();
    *Ir = steal_vector_array(Ir_vec);
    *Jr = steal_vector_array(Jr_vec);

    *len_p = Ip_vec.size();
    *Ip = steal_vector_array(Ip_vec);
    *Jp = steal_vector_array(Jp_vec);

    delete_modules(root);
}
