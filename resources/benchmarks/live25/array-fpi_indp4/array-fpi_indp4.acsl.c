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
	  loop invariant \forall integer j; 0 <= j < i ==> a[j] == (j+1)*(j+1) - j;
	  loop invariant \forall integer j; i <= j < N ==> a[j] == (j+1)*(j+1);
	  loop assigns i, a[0 .. N-1];
	  loop variant N - i;
	*/
	for(i=0;i<N;i++)
	{
		a[i]=a[i] - i;
	}
	/*@
	  loop invariant 0 <= i <= N;
	  loop invariant \forall integer j; 0 <= j < i ==> a[j] == (j+1)*(j+1) - 2*j;
	  loop invariant \forall integer j; i <= j < N ==> a[j] == (j+1)*(j+1) - j;
	  loop assigns i, a[0 .. N-1];
	  loop variant N - i;
	*/
	for(i=0;i<N;i++)
	{
		a[i]=a[i] - i;
	}
	/*@
	  loop invariant 0 <= i <= N;
	  loop invariant \forall integer j; 0 <= j < N ==> a[j] == (j+1)*(j+1) - 2*j;
	  loop assigns i;
	  loop variant N - i;
	*/
	for(i=0;i<N;i++)
	{
		//@ assert(a[i]==i*i+1);
	}
	return 1;
}
