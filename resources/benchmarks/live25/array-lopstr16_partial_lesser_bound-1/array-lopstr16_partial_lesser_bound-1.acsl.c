#include <assert.h>
#define SIZE 10000000
int a[SIZE];
int i;
int main()
{
	/*@
	  loop invariant 0 <= i <= SIZE;
	  loop invariant \forall integer j; 0 <= j < i ==> a[j] == 0;
	  loop assigns i, a[0 .. SIZE-1];
	  loop variant SIZE - i;
	*/
	for(i=0;i<SIZE;i++)
	{
	a[i] = 0 ;
	}
	/*@
	  loop invariant 0 <= i <= SIZE/2;
	  loop invariant \forall integer j; 0 <= j < i ==> a[j] == 10;
	  loop invariant \forall integer j; i <= j < SIZE ==> a[j] == 0;
	  loop assigns i, a[0 .. SIZE/2-1];
	  loop variant SIZE/2 - i;
	*/
	for(i=0;i<SIZE/2;i++)
	{
	a[i] = 10 ;
	}
	/*@
	  loop invariant 0 <= i <= SIZE/2;
	  loop invariant \forall integer j; 0 <= j < SIZE/2 ==> a[j] == 10;
	  loop assigns i;
	  loop variant SIZE/2 - i;
	*/
	for(i=0;i<SIZE/2;i++)
	{
		//@ assert(a[i]==10);
	}
	return 0;
}	
