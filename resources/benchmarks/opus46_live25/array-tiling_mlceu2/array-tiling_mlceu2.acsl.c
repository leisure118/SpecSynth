#include<limits.h>
/*@
assigns \nothing;
ensures 1 < \result < 100000;
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
		  loop invariant 1 < SIZE < 100000;
		  loop invariant \forall integer j; 0 <= j < i ==> a[j] == 0;
		  loop assigns i, a[0 .. SIZE-1];
		  loop variant SIZE - i;
		*/
		for(i=0; i<SIZE; i++)
		{
			if( i>>16 > 250)
			{
				a[i] = 1;
			}
			else
			{
				a[i] = 0;
			}
		}
		/*@
		  loop invariant 0 <= i <= SIZE;
		  loop invariant 1 < SIZE < 100000;
		  loop invariant \forall integer j; 0 <= j < SIZE ==> a[j] == 0;
		  loop assigns i;
		  loop variant SIZE - i;
		*/
		for(i=0; i<SIZE; i++)
		{
			//@ assert(a[i] == 0);
		}
	}
	return 1;
}
