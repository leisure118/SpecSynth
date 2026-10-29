#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result <= INT_MAX/4;
*/
int unknown();
#include<stdlib.h>
int N;

void __VERIFIER_assert(int x) {
    //@ assert x != 0;
    return;
}

int main()
{
	N = unknown();
	if(N <= 0) return 1;
	//@ assert (N <= 2147483647/4);
	int i;
	long long sum[1];
	long long *a = malloc(sizeof(long long)*N);
	sum[0] = 0;
	for(i=0; i<N; i++) {
		a[i] = 1;
	}
	for(i=0; i<N; i++)
	{
		sum[0] = sum[0] + a[i];
	}
	for(i=0; i<N; i++)
	{
		a[i] = a[i] + sum[0];
	}
	for(i=0; i<N; i++)
	{
		sum[0] = sum[0] + a[i];
	}
	__VERIFIER_assert(sum[0] == (long long)N*(N+2));
	return 1;
}
