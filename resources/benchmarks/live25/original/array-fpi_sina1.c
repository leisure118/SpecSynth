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
	int i;
	int sum[1];
	int *a = malloc(sizeof(int)*N);
	sum[0] = 0;
	for(i=0; i<N; i++)
	{
		sum[0] = sum[0] + 1;
	}
	for(i=0; i<N; i++)
	{
		a[i] = sum[0];
	}
	for(i=0; i<N; i++)
	{
		//@ assert(a[i] == N);
	}
	return 1;
}
