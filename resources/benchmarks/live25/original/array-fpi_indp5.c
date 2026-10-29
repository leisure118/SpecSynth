#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result <= INT_MAX/4;
*/
int unknown();
#include<stdlib.h>
int N;
int main()
{
	N = unknown();
	if(N <= 0) return 1;
	//@ assert (N <= 2147483647/4);
	long long i;
	long long *a = malloc(sizeof(long long)*N);
	long long sum[1];
	sum[0] = 0;
	for(i=0;i<N;i++)
	{
		a[i]=((i+1)*(i+1));
	}
	for(i=0;i<N;i++)
	{
		a[i]=a[i]-(i*i);
	}
	for(i=0;i<N;i++)
	{
		a[i]=a[i]-i;
	}
	for(i=0;i<N;i++)
	{
		a[i]=a[i]-i;
	}
	for(i=0;i<N;i++)
	{
		sum[0] = sum[0] + a[i];
	}
	//@ assert(sum[0] == N);
	return 1;
}
