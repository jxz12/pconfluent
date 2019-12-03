%module pgd
%{
    #define SWIG_FILE_WITH_INIT
    #include "../pgd.hpp"
%}

%include "numpy.i"
%init %{
    import_array();
%}

// edge indices
%apply (int* IN_ARRAY1, int DIM1){(int* I, int len_I),
                                  (int* J, int len_J)}

// requires memory 'leak'
%apply (int** ARGOUTVIEWM_ARRAY1, int* DIM1){(int** Ir, int* len_Ir),
                                             (int** Jr, int* len_Jr),
                                             (int** Ip, int* len_Ip),
                                             (int** Jp, int* len_Jp)}

#include "../pgd.hpp"

%include exception.i
%rename (routing_swig) np_routing;
%exception np_routing {
    try {
        $action
    } catch (std::invalid_argument e) {
        SWIG_exception(SWIG_RuntimeError, e.what());
    }
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

