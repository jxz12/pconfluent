#include "pgd.cpp"

int main()
{
    int I[] = { 0,0,1,1 };
    int J[] = { 2,3,2,3 };

    module* super = init_modules_undirected(4, 4, I, J);
    print_dfs(super);
}
