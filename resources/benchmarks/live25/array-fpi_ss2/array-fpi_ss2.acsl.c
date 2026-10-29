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
	long long sum[1];
	long long *a = malloc(sizeof(long long)*N);
	/*@
	  admit \valid(a+(0 .. N-1));
	*/
	sum[0] = 0;
	/*@
	  loop invariant 0 <= i <= N;
	  loop invariant \forall integer j; 0 <= j < i ==> a[j] == 1;
	  loop assigns i, a[0 .. N-1];
	  loop variant N - i;
	*/
	for(i=0; i<N; i++)
	{
		a[i] = 1;
	}
	/*@
	  loop invariant 0 <= i <= N;
	  loop invariant \forall integer j; 0 <= j < N ==> a[j] == 1;
	  loop invariant sum[0] == i;
	  loop assigns i, sum[0];
	  loop variant N - i;
	*/
	for(i=0; i<N; i++)
	{
		sum[0] = sum[0] + a[i];
	}
	/*@
	  loop invariant 0 <= i <= N;
	  loop invariant \forall integer j; 0 <= j < i ==> a[j] == 0;
	  loop invariant sum[0] == N;
	  loop assigns i, a[0 .. N-1];
	  loop variant N - i;
	*/
	for(i=0; i<N; i++)
	{
		a[i] = 0;
	}
	/*@
	  loop invariant 0 <= i <= N;
	  loop invariant \forall integer j; 0 <= j < i ==> a[j] == N;
	  loop invariant \forall integer j; i <= j < N ==> a[j] == 0;
	  loop invariant sum[0] == N;
	  loop assigns i, a[0 .. N-1];
	  loop variant N - i;
	*/
	for(i=0; i<N; i++)
	{
		a[i] = a[i] + sum[0];
	}
	/*@
	  loop invariant 0 <= i <= N;
	  loop invariant \forall integer j; 0 <= j < N ==> a[j] == N;
	  loop invariant sum[0] == N + i*N;
	  loop assigns i, sum[0];
	  loop variant N - i;
	*/
	for(i=0; i<N; i++)
	{
		sum[0] = sum[0] + a[i];
	}
	/*@
	  loop invariant 0 <= i <= N;
	  loop invariant \forall integer j; 0 <= j < i ==> a[j] == N*(N+2);
	  loop invariant \forall integer j; i <= j < N ==> a[j] == N;
	  loop invariant sum[0] == N*(N+1);
	  loop assigns i, a[0 .. N-1];
	  loop variant N - i;
	*/
	for(i=0; i<N; i++)
	{
		a[i] = a[i] + sum[0];
	}
	/*@
	  loop invariant 0 <= i <= N;
	  loop invariant \forall integer j; 0 <= j < N ==> a[j] == N*(N+2);
	  loop invariant sum[0] == N*(N+1);
	  loop assigns i;
	  loop variant N - i;
	*/
	for(i=0; i<N; i++)
	{
		//@ assert(a[i] == (long long)N*(N+2));
		__VERIFIER_assert(a[i] == (long long)N*(N+2));
	}
	return 1;
}
