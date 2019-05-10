#include "pgd.cpp"

int main()
{
    // int I[] = { 0,0,0,1,1,1,2 };
    // int J[] = { 2,3,4,2,3,4,3 };
    // module* root = new module(5, 7, I, J);

    // int I[] = { 0,0,0,1,1,1,2,2,2 };
    // int J[] = { 3,4,5,3,4,5,3,4,5 };
    // module* root = new module(6, 9, I, J);

    int I[] = { 0,0,0,0, 1,1,1, 2,2, 3,3,3, 4,4,4, 5 };
    int J[] = { 1,2,3,4, 2,6,7, 6,7, 4,6,7, 5,6,7, 6 };
    module* root = new module(8, 16, I, J);

    // pgd(root, 3,3,2);
     pgd(root, 1,0,999);

    vector<int> Ir, Jr, Ip, Jp;
    routing(root, Ir, Jr, Ip, Jp);
    
    delete_modules(root);
}
