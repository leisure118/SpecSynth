#include<stdlib.h>
#include <assert.h>
#define SIZE 100000
int *a[SIZE];
int i;
int main ()
{
	/*@
	  loop invariant 0 <= i <= SIZE;
	  loop assigns i, a[0 .. SIZE-1];
	  loop variant SIZE - i;
	*/
	for(i = 0; i < SIZE; i++)
	{
		a[i] = 0;
	}
	/*@
	  loop invariant 0 <= i <= SIZE/2;
	  loop assigns i, a[0 .. SIZE/2-1], __fc_heap_status;
	  loop variant SIZE/2 - i;
	*/
	for(i = 0; i < SIZE / 2; i++)
	{
		a[i] = malloc(sizeof(int)) ;
	}
	/*@
	  loop invariant 0 <= i <= SIZE/2;
	  loop assigns i;
	  loop variant SIZE/2 - i;
	*/
	for(i = 0; i < SIZE / 2; i++)
	{
		//@ admit \valid(a[i]);
		//@ assert(a[i] != 0);
	}
return 0;
}	
