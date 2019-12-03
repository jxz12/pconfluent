#ifndef PGD_HPP
#define PGD_HPP

#include <vector>
#include <unordered_set>
using std::vector;
using std::unordered_set;

///////////////////////
// visible to python //
///////////////////////
void routing_swig(int n, int m, int* I, int* J,
                  int* len_r, int** Ir, int** Jr, int* len_p, int** Ip, int** Jp,
                  int w_intersect, int w_difference);

//////////////
// cpp only //
//////////////
struct module
{
    int idx;
    unordered_set<module*> neighbours;
    unordered_set<module*> children;

    module(int idx);
    module(int n, int m, int* I, int* J, int idx=-1);
};
void delete_modules(module* root);

void pgd(module* root, int w_intersect, int w_difference);
module* merge(module* m, module* n, int new_module_idx);
unsigned intersect(module* m, module* n);
unsigned intersect(unordered_set<module*>& Nm, unordered_set<module*>& Nn);
int difference(module* m, module* n, int size_intersect);

void reindex_modules(module* root, int& new_idx);
void reindex_modules_contiguous(module* root, int n_leaves);
int* steal_vector_array(vector<int>& v);

void construct_routing(const module* root, vector<int>& Ir, vector<int>& Jr, vector<int>& Ip, vector<int>& Jp);
void add_routing_edges(const module* parent, vector<int>& Ir, vector<int>& Jr);
void add_power_edges(const module* parent, vector<int>& Ip, vector<int>& Jp);

#endif
