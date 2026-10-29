#include <stddef.h>
/*@
  requires \valid(array + (0 .. length-1));
  assigns \nothing;
  ensures \result == NULL || *\result == element;
*/
int* search(int* array, size_t length, int element) {
	/*@
	  loop invariant 0 <= i <= length;
	  loop invariant \forall integer j; 0 <= j < i ==> array[j] != element;
	  loop assigns i;
	  loop variant length - i;
	*/
	for(size_t i = 0; i < length; i++) 
		if(array[i]==element) return &array[i];
	return NULL;
}
void main() {
	int a[] = {1, 5, 6, 7};
	int* res = search(a, 4, 5);
}