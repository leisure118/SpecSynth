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
		int val2 = 3;
		int val1 = 0;
		int low=2;
		for(i = 0; i < SIZE; i++)
		{
			if(i+1 < SIZE)
			{
				a[i+1] = val1;
			}
			a[i] = val2;
		}
		for(i = 0; i < SIZE; i++)
		{
			//@ assert(a[i] >= low);
		}
	}
	return 1;
}
