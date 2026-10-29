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
		for(i=0; i<SIZE; i++)
		{
			//@ assert(a[i] == 0);
		}
	}
	return 1;
}
