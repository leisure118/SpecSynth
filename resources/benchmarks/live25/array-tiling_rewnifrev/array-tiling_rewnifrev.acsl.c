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
		int i;
		int *a = malloc(sizeof(int)*SIZE);
		/*@
		  loop invariant SIZE-1 >= i >= -1;
		  loop invariant \forall integer j; i < j < SIZE ==> a[j] == j;
		  loop assigns i, a[0 .. SIZE-1];
		  loop variant i+1;
		*/
		for( i=SIZE-1; i>=0; i-- )
		{
			if((i-1) >= 0 )
			{
				a[i-1] = i-2;
			}
			a[i] = i;
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
