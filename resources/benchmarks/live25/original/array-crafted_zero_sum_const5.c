#include<stdlib.h>
/*@
	assigns \nothing;
	ensures 1 < \result < 100000;
*/
int unknown();
long SIZE;
const int MAX = 100000;
int main()
{
	SIZE = unknown();
	if(SIZE > 1 && SIZE < MAX)
	{
		int i;
		long *a = malloc(sizeof(long)*SIZE);
		long sum=0;
		for(i = 0; i < SIZE; i++ )
		{
			a[i] = 1;
		}
		for(i = 0; i < SIZE; i++ )
		{
			sum = sum + a[i];
		}
		for(i = 0; i < SIZE; i++)
		{
			sum = sum - a[i];
		}
		for(i = 0; i < SIZE; i++ )
		{
			sum = sum + a[i];
		}
		for(i = 0; i < SIZE; i++)
		{
			sum = sum - a[i];
		}
		for(i = 0; i < SIZE; i++ )
		{
			sum = sum + a[i];
		}
		for(i = 0; i < SIZE; i++)
		{
			sum = sum - a[i];
		}
		for(i = 0; i < SIZE; i++ )
		{
			sum = sum + a[i];
		}
		for(i = 0; i < SIZE; i++)
		{
			sum = sum - a[i];
		}
		for(i = 0; i < SIZE; i++ )
		{
			sum = sum + a[i];
		}
		for(i = 0; i < SIZE; i++)
		{
			sum = sum - a[i];
		}
		//@ assert(sum == 0);
	}
	return 1;
}
