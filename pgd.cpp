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

    module(int idx);
    module(int n, int m, int* I, int* J);
};
void delete_dfs(module* root);

int nedges(const unordered_set<module*>& Nm, const unordered_set<module*>& Nn);
int nedges(const module* m, const module* n);
void pgd(module* root, int edge_score=1, int module_score=1, int crossing_score=1);

void routing(const module* root, vector<int>& Ir, vector<int>& Jr, vector<int>& Ip, vector<int>& Jp);
void add_power_edges(const module* parent, vector<int>& Ip, vector<int>& Jp);
void add_routing_edges(const module* parent, vector<int>& Ir, vector<int>& Jr);


module::module(int idx) : idx(idx), neighbours(), children()
{}

// this initializes the module into a super module connected to trivial top modules
module::module(int n, int m, int* I, int* J) : idx(n)
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

void delete_dfs(module* parent)
{
    for (auto child : parent->children)
    {
        delete_dfs(child);
    }
    delete parent;
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
void pgd(module* root, int edge_score, int module_score, int crossing_score)
{
    int new_module_idx = root->idx + 1; // assumes that root index is bigger than all leaves
    while (true)
    {
        std::cerr << new_module_idx<< std::endl;

        module* best1;
        module* best2;
        int best_score=0;
        int best_intersect=0;
        // TODO: store these scores in memory to reduce computation

        // find best merge
        for (auto child1 : root->children)
        {
            for (auto child2 : root->children)
            {
                if (child1->idx >= child2->idx) // don't do the same pair redundantly
                    continue;

                int intersect = nedges(child1, child2);

                // check for crossings
                int diff1 = child1->neighbours.size() - intersect;
                int diff2 = child2->neighbours.size() - intersect;
                bool connected = child1->neighbours.find(child2) != child1->neighbours.end();

                //bool merge1 = (child1->children.size()!=0) && (diff1!=0);
                //bool merge2 = (child2->children.size()!=0) && (diff2!=0);

                // check for extra module weights
                // don't penalise when a child is a leaf, because it cannot be merged
                bool mod1 = (child1->children.size()==0) || (diff1==0);
                bool mod2 = (child2->children.size()==0) || (diff2==0);

                // add points for edges and modules
                int score = intersect * edge_score
                            + ((mod1?1:0)+(mod2?1:0)-1) * module_score
                            - ((diff1+diff2)-(connected?2:0)) * crossing_score;
                            // TODO: be sure that this crossing score makes sense

                std::cerr << child1->idx << " " << child2->idx << " " << score << std::endl;
                
                if (score > best_score)
                {
                    best1 = child1;
                    best2 = child2;
                    best_score = score;
                    best_intersect = intersect;
                }
            }
        }
        // TODO: possible infinite loop
        if (best_score == 0)
            break;

        // perform the merge itself
        bool merge1 = (best1->children.size()!=0) && (best1->neighbours.size()==best_intersect);
        bool merge2 = (best2->children.size()!=0) && (best2->neighbours.size()==best_intersect);
        
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
                neighbour->neighbours.erase(best1);
                neighbour->neighbours.erase(best2);
                neighbour->neighbours.insert(best1);
            }
            best1->children.insert(best2);
            root->children.erase(best2);
        }
        else if (merge2)
        {
            // above vice versa
            for (auto neighbour : best2->neighbours)
            {
                best1->neighbours.erase(neighbour);
                neighbour->neighbours.erase(best1);
                neighbour->neighbours.erase(best2);
                neighbour->neighbours.insert(best1);
            }
            best2->children.insert(best1);
            root->children.erase(best1);
        }
        else // new module
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

// Ir & Jr are routing edges, Ip & Jp are power edges
// these are all output parameters
void routing(const module* root, vector<int>& Ir, vector<int>& Jr, vector<int>& Ip, vector<int>& Jp)
{
    for (auto top : root->children) // 'throw away' root
    {
        std::cerr << top->idx << std::endl;
        add_routing_edges(top, Ir, Jr);
        add_power_edges(top, Ip, Jp);
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
