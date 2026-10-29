#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result <= INT_MAX/4;
*/
int unknown();
#include<stdlib.h>
int N;

/*@ requires x != 0; */
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
	/*@
	  loop invariant 0 <= i <= N;
	  loop invariant \forall integer j; 0 <= j < i ==> a[j] == 1;
	  loop assigns i, a[0 .. N-1];
	  loop variant N - i;
	*/
	for(i=0; i<N; i++) {
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
	  loop invariant \forall integer j; 0 <= j < i ==> a[j] == N + 1;
	  loop invariant \forall integer j; i <= j < N ==> a[j] == 1;
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
	  loop invariant \forall integer j; 0 <= j < N ==> a[j] == N + 1;
	  loop invariant sum[0] == N + i*(N+1LL);
	  loop assigns i, sum[0];
	  loop variant N - i;
	*/
	for(i=0; i<N; i++)
	{
		sum[0] = sum[0] + a[i];
	}
	__VERIFIER_assert(sum[0] == (long long)N*(N+2));
	return 1;
}
