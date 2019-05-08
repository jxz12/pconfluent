#include "pgd.cpp"

int main()
{
    int I[] = { 0,0,0,1,1,1,2 };
    int J[] = { 2,3,4,2,3,4,3 };

    module* super = init_modules_undirected(5, 7, I, J);
    pgd(super);
    print_dfs(super);
}
