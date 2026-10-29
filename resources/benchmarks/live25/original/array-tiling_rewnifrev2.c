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
		for( i=SIZE-2; i >= 0; i-- )
		{
			a[i] = i;
			a[i+1] = i+1;
		}
		for(i = 0; i < SIZE; i++)
		{
			//@ assert(a[i] >= i );
		}
	}
	return 1;
}
