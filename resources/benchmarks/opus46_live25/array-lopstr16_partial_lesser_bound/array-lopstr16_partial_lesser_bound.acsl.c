#include<stdlib.h>
#include <assert.h>
#define SIZE 1000000
int *a[SIZE];
int i;
int main()
{
	/*@
	  loop invariant 0 <= i <= SIZE;
	  loop invariant \forall integer j; 0 <= j < i ==> a[j] == \null;
	  loop assigns i, a[0 .. SIZE-1];
	  loop variant SIZE - i;
	*/
	for(i = 0; i < SIZE; i++)
	{
		a[i] = 0;
	}
	/*@
	  loop invariant 0 <= i <= SIZE / 2;
	  loop invariant \forall integer j; 0 <= j < i ==> \valid(a[j]);
	  loop assigns i, a[0 .. SIZE/2 - 1], __fc_heap_status;
	  loop variant SIZE / 2 - i;
	*/
	for(i = 0; i < SIZE / 2; i++)
	{
		a[i] = malloc(sizeof(int)) ;
		//@ admit \valid(a[i]);
	}
	/*@
	  loop invariant 0 <= i <= SIZE / 2;
	  loop invariant \forall integer j; 0 <= j < SIZE/2 ==> \valid(a[j]);
	  loop assigns i;
	  loop variant SIZE / 2 - i;
	*/
	for(i = 0; i < SIZE / 2; i++)
	{
		//@ assert(a[i] != 0);
	}
	return 0;
}	
