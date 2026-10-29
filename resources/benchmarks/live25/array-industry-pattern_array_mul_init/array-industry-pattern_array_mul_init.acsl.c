#include <assert.h>
#include <limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#define SIZE 100000
int main()
{
	int a[SIZE];
	int b[SIZE];
	int k;
	int i;
	//@ admit \separated(a+(0 .. SIZE-1), b+(0 .. SIZE-1));
	/*@
	  loop invariant 0 <= i <= SIZE;
	  loop invariant \forall integer j; 0 <= j < i ==> a[j] == j;
	  loop invariant \forall integer j; 0 <= j < i ==> b[j] == j;
	  loop assigns i, k, a[0 .. SIZE-1], b[0 .. SIZE-1];
	  loop variant SIZE - i;
	*/
	for (i  = 0; i<SIZE ; i++)
	{
		a[i] = i; 
		b[i] = i ;
	}
	/*@
	  loop invariant 0 <= i <= SIZE;
	  loop invariant \forall integer j; 0 <= j < i ==> (a[j] == b[j] || b[j] == a[j] * a[j]);
	  loop invariant \forall integer j; i <= j < SIZE ==> (a[j] == j && b[j] == j);
	  loop assigns i, k, a[0 .. SIZE-1], b[0 .. SIZE-1];
	  loop variant SIZE - i;
	*/
	for (i=0; i< SIZE; i++)
	{
		if(unknown())
		{
			k = unknown();
			a[i] = k;
			b[i] = k * k ;
		}
	}
	/*@
	  loop invariant 0 <= i <= SIZE;
	  loop invariant \forall integer j; 0 <= j < SIZE ==> (a[j] == b[j] || b[j] == a[j] * a[j]);
	  loop assigns i;
	  loop variant SIZE - i;
	*/
	for (i=0; i< SIZE; i++)
	{
		//@ assert(a[i] == b[i] || b[i]  == a[i] * a[i]);
	}
}
