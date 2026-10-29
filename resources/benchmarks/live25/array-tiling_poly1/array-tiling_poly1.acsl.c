#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include<stdlib.h>
int SIZE;
const int MAX = 100000;
int main()
{
	SIZE = unknown();
	if(SIZE > 1 && SIZE < MAX)
	{
		long long i;
		long long *a = malloc(sizeof(long long)*SIZE);
		/*@
		  loop invariant 0 <= i <= SIZE;
		  loop invariant \forall integer j; 0 <= j < i ==> a[j] == j*j;
		  loop assigns i, a[0 .. SIZE-1];
		  loop variant SIZE - i;
		*/
		for(i=0; i<SIZE; i++)
		{
			a[i] = i*i;
		}
		/*@
		  loop invariant 0 <= i <= SIZE;
		  loop invariant \forall integer j; 0 <= j < SIZE ==> a[j] == j*j;
		  loop assigns i;
		  loop variant SIZE - i;
		*/
		for(i=0; i<SIZE; i++)
		{
			//@ assert(a[i] == i*i);
		}
	}
	return 1;
}
