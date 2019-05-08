#include "pgd.cpp"

int main()
{
    int I[] = { 0,0,0,1,1,1,2 };
    int J[] = { 2,3,4,2,3,4,3 };

    module* root = new module(5, 7, I, J);
    pgd(root);

    vector<int> Ir, Jr, Ip, Jp;
    routing(root, Ir, Jr, Ip, Jp);
    
    delete root;
}
