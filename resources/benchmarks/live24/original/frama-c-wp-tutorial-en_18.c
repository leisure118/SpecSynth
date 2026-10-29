#include <stddef.h>
#include <limits.h>
int* search(int* array, size_t length, int element){
    for(size_t i = 0; i < length; i++){
        if(array[i] == element) return &array[i];
    }
    return NULL;
}
int main(){
    int array[] = {1,2,3,4,5};
    int *p = search(array,5,6);
    //@ assert p == NULL;
}