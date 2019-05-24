%module pgd
%{
    #define SWIG_FILE_WITH_INIT
    extern void routing_swig(int n, int m, int* I, int* J,
                             int* len_r, int** Ir, int** Jr, int* len_p, int** Ip, int** Jp,
                             int w_intersect=3, int w_difference=1);
%}

%include "numpy.i"
%init %{
    import_array();
%}

// edge indices
%apply (int* IN_ARRAY1, int DIM1){(int* I, int len_I),
                                  (int* J, int len_J)}

// output edge indices
//%apply (int* ARGOUT_ARRAY1, int DIM1){(int* Ir, int len_Ir),
//                                      (int* Jr, int len_Jr),
//                                      (int* Ip, int len_Ip),
//                                      (int* Jp, int len_Jp)}
%apply (int** ARGOUTVIEWM_ARRAY1, int* DIM1){(int** Ir, int* len_Ir),
                                             (int** Jr, int* len_Jr),
                                             (int** Ip, int* len_Ip),
                                             (int** Jp, int* len_Jp)}

extern void routing_swig(int n, int m, int* I, int* J,
                         int* len_r, int** Ir, int** Jr, int* len_p, int** Ip, int** Jp,
                         int w_intersect=3, int w_difference=1);

%rename (routing_swig) np_routing;
%exception np_routing {
    $action
    if (PyErr_Occurred()) SWIG_fail;
}

%inline %{
    void np_routing(int n,
                    int* I, int len_I,
                    int* J, int len_J,
                    int** Ir, int* len_Ir,
                    int** Jr, int* len_Jr,
                    int** Ip, int* len_Ip,
                    int** Jp, int* len_Jp,
                    int w_intersect, int w_difference) {

        if (len_I != len_J) {
            PyErr_Format(PyExc_ValueError, "arrays of indices do not have same length");
            return;
        }
        routing_swig(n, len_I, I, J, len_Ir, Ir, Jr, len_Ip, Ip, Jp, w_intersect, w_difference);
        *len_Jr = *len_Ir;
        *len_Jp = *len_Ip;
    }
%}

