%module pgd
%{
    #define SWIG_FILE_WITH_INIT
    extern void routing(int n, int m, int* I, int* J, int* Ir, int* Jr, int* Ip, int* Jp);
%}

%include "numpy.i"
%init %{
    import_array();
%}

// edge indices
%apply (int* IN_ARRAY1, int DIM1){(int* I, int len_I),
                                  (int* J, int len_J)}

// output edge indices
%apply (int* ARGOUT_ARRAY1, int DIM1){(int* Ir, int len_Ir),
                                      (int* Jr, int len_Jr),
                                      (int* Ip, int len_Ip),
                                      (int* Jp, int len_Jp)}

extern void routing(int n, int m, int* I, int* J, int* Ir, int* Jr, int* Ip, int* Jp);

%rename (routing) np_routing;
%exception np_routing {
    $action
    if (PyErr_Occurred()) SWIG_fail;
}

%inline %{
    void np_routing(int n,
                    int* I, int len_I,
                    int* J, int len_J,
                    int* Ir, int len_Ir,
                    int* Jr, int len_Jr,
                    int* Ip, int len_Ip,
                    int* Jp, int len_Jp) {

        if (len_I != len_J) {
            PyErr_Format(PyExc_ValueError, "arrays of indices do not have same length");
            return;
        }
        routing(n, len_I, I, J, Ir, Jr, Ip, Jp);
    }
%}

