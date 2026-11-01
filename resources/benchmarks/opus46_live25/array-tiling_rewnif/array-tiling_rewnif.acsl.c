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
		//@ admit \valid(a+(0 .. SIZE-1));
		/*@
		  loop invariant 0 <= i <= SIZE;
		  loop invariant \forall integer j; 0 <= j < i ==> a[j] == j;
		  loop assigns i, a[0 .. SIZE-1];
		  loop variant SIZE - i;
		*/
		for( i = 0; i < SIZE ; i++ )
		{
			if((i+1) < SIZE )
			{
				a[i+1] = i;
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
