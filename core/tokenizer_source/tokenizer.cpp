#include <Python.h>
#include <vector>

#include "tokenizer.h"

using namespace std;


static PyObject *_tokenize(PyObject *self, PyObject *args) {
        PyObject * container;
        char * the_string;
        int string_size;
        if (! PyArg_ParseTuple(args, "s#O", &the_string, &string_size, &container)) return NULL;

        string text(the_string);

        long int num_items = PySequence_Size(container);

        if (num_items < 0) return NULL; // Not a list

        container = PySequence_Fast(container, "expected a sequence");
        // build the vector of strings
        vector<string> keyterms(num_items);
        for (unsigned int i = 0; i < num_items; i++) {
                // grab the string object from the next element of the list
                PyObject * strObj = PySequence_Fast_GET_ITEM(container, i);
                char * string;
                int size;

                // make it a string
                PyArg_Parse(strObj, "s#", &string, &size);
                keyterms[i] = string;
        }
        Py_DECREF(container);  // confirmed leakage without this call.
        vector<string> tokens = tokenize(the_string, keyterms);

        // build the Python list back
        PyObject *PList = PyList_New(tokens.size());
        for (unsigned int i = 0; i < tokens.size(); i++) {
                PyList_SetItem(PList, i, Py_BuildValue("s#", tokens[i].c_str(), tokens[i].size()));
        }

        return PList;
}


static PyMethodDef Methods[] = {
        {"tokenize", _tokenize, METH_VARARGS,
         "Tokenizes a string guaranteeing that tokens in the set are preserved."},
        {NULL, NULL, 0, NULL}
};


static struct PyModuleDef module = {
        PyModuleDef_HEAD_INIT,
        "_tokenizer", NULL, -1, Methods
};


PyMODINIT_FUNC
PyInit__tokenizer(void)
{
        return PyModule_Create(&module);
}
