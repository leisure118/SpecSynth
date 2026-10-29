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
	//@ admit \valid(a+(0 .. N-1));
	sum[0] = 0;
	/*@
	  loop invariant 0 <= i <= N;
	  loop invariant sum[0] == i;
	  loop assigns i, sum[0];
	  loop variant N - i;
	*/
	for(i=0; i<N; i++)
	{
		sum[0] = sum[0] + 1;
	}
	/*@
	  loop invariant 0 <= i <= N;
	  loop invariant sum[0] == N;
	  loop invariant \forall integer j; 0 <= j < i ==> a[j] == N;
	  loop assigns i, a[0 .. N-1];
	  loop variant N - i;
	*/
	for(i=0; i<N; i++)
	{
		a[i] = sum[0];
	}
	/*@
	  loop invariant 0 <= i <= N;
	  loop invariant \forall integer j; 0 <= j < N ==> a[j] == N;
	  loop assigns i;
	  loop variant N - i;
	*/
	for(i=0; i<N; i++)
	{
		//@ assert(a[i] % N == 0);
	}
	return 1;
}
