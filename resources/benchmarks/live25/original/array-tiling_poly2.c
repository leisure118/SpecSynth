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
		long long i;
		long long *a = malloc(sizeof(long long)*SIZE);
		for(i=0; i<SIZE; i++)
		{
			a[i] = i*i + 2;
		}
		for(i=0; i<SIZE; i++)
		{
			a[i] = a[i] - 2;
		}
		for(i=0; i<SIZE; i++)
		{
			//@ assert(a[i] == i*i);
		}
	}
	return 1;
}
