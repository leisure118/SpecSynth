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
		for( i = 0; i < SIZE ; i++ )
		{
			if((i+1) < SIZE )
			{
				a[i+1] = i;
			}
			a[i] = i;
		}
		for(i = 0; i < SIZE; i++)
		{
			//@ assert(a[i] >= i );
		}
	}
	return 1;
}
