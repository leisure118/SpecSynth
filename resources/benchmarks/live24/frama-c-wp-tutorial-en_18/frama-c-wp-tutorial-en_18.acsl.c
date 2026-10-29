#include <stddef.h>
#include <limits.h>
/*@
  requires length > 0;
  requires \valid(array + (0 .. length-1));
  assigns \nothing;
  ensures \result == NULL || (\exists integer i; 0 <= i < length && \result == &array[i] && *\result == element);
*/
int* search(int* array, size_t length, int element){
    /*@
      loop invariant 0 <= i <= length;
      loop invariant \forall integer j; 0 <= j < i ==> array[j] != element;
      loop assigns i;
      loop variant length - i;
    */
    for(size_t i = 0; i < length; i++){
        if(array[i] == element) return &array[i];
    }
    return NULL;
}
int main(){
    int array[] = {1,2,3,4,5};
    int *p = search(array,5,6);
    //@ assert \forall integer j; 0 <= j < 5 ==> array[j] != 6;
    //@ assert p == NULL;
}