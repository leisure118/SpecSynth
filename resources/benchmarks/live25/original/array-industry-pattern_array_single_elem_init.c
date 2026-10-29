#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include <assert.h>
#define SIZE 100000
int unknown();
int main()
{
	int i;
	int a[SIZE];
	int b[SIZE];
	int c[SIZE];
	for (i = 0; i < SIZE; i++)
	{
		int q = unknown();
		a[i] = 0;
		if (q == 0)
		{
			a[i] = 1;
			b[i] = i % 2;
		}
		if (a[i] != 0)
		{
			if (b[i] == 0)
			{
				c[i] = 0;
			}
			else
			{
				c[i] = 1;
			}
		}
	}
	a[15000] = 1;
	for (i = 0; i < SIZE; i++)
	{
		if (i == 15000 )
		{
			//@ assert(c[i] == 0);
		}
	}
	return 0;
}
