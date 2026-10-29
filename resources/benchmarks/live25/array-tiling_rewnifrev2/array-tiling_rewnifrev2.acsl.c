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
	int i;
	if(SIZE > 1 && SIZE < MAX)
	{
		int *a = malloc(sizeof(int)*SIZE);
		/*@
		  loop invariant -1 <= i <= SIZE-2;
		  loop invariant (i == SIZE-2) || \forall integer j; i+1 <= j < SIZE ==> a[j] == j;
		  loop assigns i, a[0 .. SIZE-1];
		  loop variant i + 1;
		*/
		for( i=SIZE-2; i >= 0; i-- )
		{
			a[i] = i;
			a[i+1] = i+1;
		}
		/*@
		  loop invariant 0 <= i <= SIZE;
		  loop invariant \forall integer j; 0 <= j < SIZE ==> a[j] == j;
		  loop assigns i;
		  loop variant SIZE - i;
		*/
		for(i = 0; i < SIZE; i++)
		{
			//@ assert(a[i] >= i );
		}
	}
	return 1;
}
