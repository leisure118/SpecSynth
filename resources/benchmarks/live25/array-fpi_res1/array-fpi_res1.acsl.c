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
	int *a = malloc(sizeof(int)*N);
	int *b = malloc(sizeof(int)*N);
	sum[0] = 0;
	/*@
	  admit \separated(a+(0 .. N-1), b+(0 .. N-1));
	*/
	/*@
	  admit \valid(b+(0 .. N-1));
	*/
	/*@
	  admit \valid(a+(0 .. N-1));
	*/
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
	  loop invariant \forall integer j; 0 <= j < i ==> b[j] == 1;
	  loop invariant \forall integer j; 0 <= j < N ==> a[j] == 1;
	  loop assigns i, b[0 .. N-1];
	  loop variant N - i;
	*/
	for(i=0; i<N; i++)
	{
		b[i] = 1;
	}
	/*@
	  loop invariant 0 <= i <= N;
	  loop invariant \forall integer j; 0 <= j < N ==> a[j] == 1;
	  loop invariant \forall integer j; 0 <= j < N ==> b[j] == 1;
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
	  loop invariant \forall integer j; 0 <= j < N ==> a[j] == 1;
	  loop invariant \forall integer j; 0 <= j < N ==> b[j] == 1;
	  loop invariant sum[0] == N + i;
	  loop assigns i, sum[0];
	  loop variant N - i;
	*/
	for(i=0; i<N; i++)
	{
		sum[0] = sum[0] + b[i];
	}
	//@ assert(sum[0] <= 2*N);
	return 1;
}
