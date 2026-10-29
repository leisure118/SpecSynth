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
/*@
	  loop invariant 0 <= i <= N;
	  loop invariant \forall integer j; 0 <= j < i ==> a[j] == (j+1)*(j+1);
	  loop assigns i, a[0 .. N-1];
	  loop variant N - i;
	*/
	for(i=0;i<N;i++)
	{
		a[i]=((i+1)*(i+1));
	}
	/*@
	  loop invariant 0 <= i <= N;
	  loop invariant \forall integer j; 0 <= j < i ==> a[j] == 2*j + 1;
	  loop invariant \forall integer j; i <= j < N ==> a[j] == (j+1)*(j+1);
	  loop assigns i, a[0 .. N-1];
	  loop variant N - i;
	*/
	for(i=0;i<N;i++)
	{
		a[i]=a[i]-(i*i);
	}
	/*@
	  loop invariant 0 <= i <= N;
	  loop invariant \forall integer j; 0 <= j < i ==> a[j] == j + 1;
	  loop invariant \forall integer j; i <= j < N ==> a[j] == 2*j + 1;
	  loop assigns i, a[0 .. N-1];
	  loop variant N - i;
	*/
	for(i=0;i<N;i++)
	{
		a[i]=a[i]-i;
	}
	/*@
	  loop invariant 0 <= i <= N;
	  loop invariant \forall integer j; 0 <= j < i ==> a[j] == 1;
	  loop invariant \forall integer j; i <= j < N ==> a[j] == j + 1;
	  loop assigns i, a[0 .. N-1];
	  loop variant N - i;
	*/
	for(i=0;i<N;i++)
	{
		a[i]=a[i]-i;
	}
	/*@
	  loop invariant 0 <= i <= N;
	  loop invariant sum[0] == i;
	  loop invariant \forall integer j; 0 <= j < N ==> a[j] == 1;
	  loop assigns i, sum[0];
	  loop variant N - i;
	*/
	for(i=0;i<N;i++)
	{
		sum[0] = sum[0] + a[i];
	}
	//@ assert(sum[0] == N);
	return 1;
}
