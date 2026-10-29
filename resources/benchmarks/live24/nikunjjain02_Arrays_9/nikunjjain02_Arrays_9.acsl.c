#include<stddef.h>
/*@
  requires length >= 0;
  requires \valid(array + (0 .. length-1));
  assigns array[0 .. length-1];
  ensures \forall integer j; 0 <= j < length && \old(array[j]) == old ==> array[j] == new;
  ensures \forall integer j; 0 <= j < length && \old(array[j]) != old ==> array[j] == \old(array[j]);
*/
void search_and_replace(int* array, size_t length, int old, int new) {
	/*@
	  loop invariant 0 <= i <= length;
	  loop invariant \forall integer j; 0 <= j < i ==> array[j] == (\at(array[j], LoopEntry) == old ? new : \at(array[j], LoopEntry));
	  loop invariant \forall integer j; i <= j < length ==> array[j] == \at(array[j], LoopEntry);
	  loop assigns i, array[0 .. length-1];
	  loop variant length - i;
	*/
	for(size_t i = 0;i < length; ++i) {
		if(array[i]==old) array[i]=new;
	}
}
void main() {
	int a[] = {1, 2, 4, 5};
	search_and_replace(a, 4, 2, 3);
	//@ assert a[0] == 1 && a[1] == 3 && a[2] == 4 && a[3] == 5;
}