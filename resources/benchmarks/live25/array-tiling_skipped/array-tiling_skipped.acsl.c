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
	      loop assigns i, a[0 .. SIZE-1];
	      loop variant SIZE - i;
	    */
	    for(i = 0; i < SIZE; i++)
		{
		    a[i] = unknown();
		}
		if(SIZE % 2 != 0) { return 1; }
		//@ assert(SIZE % 2 == 0);
		/*@
		  loop invariant 1 <= i <= SIZE/2 + 1;
		  loop invariant \forall integer j; 0 <= j < 2*i - 2 ==> a[j] <= j;
		  loop assigns i, a[0 .. SIZE-1];
		  loop variant SIZE/2 + 1 - i;
		*/
		for(i = 1; i <= SIZE/2; i++ )
		{
			if( a[2*i-2] > 2*i-2 )
			{
				a[2*i-2] = 2*i-2;
			}
			if( a[2*i-1] > 2*i-1 )
			{
				a[2*i-1] = 2*i-1;
			}
		}
		/*@
		  loop invariant 0 <= i <= SIZE;
		  loop invariant \forall integer j; 0 <= j < SIZE ==> a[j] <= j;
		  loop assigns i;
		  loop variant SIZE - i;
		*/
		for(i = 0; i < SIZE; i++)
		{
			//@ assert(a[i] <= i);
		}
	}
	return 1;
}
