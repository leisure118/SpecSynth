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
	long long *b = malloc(sizeof(long long)*N);
		/*@ admit \valid(a+(0 .. N-1)); */
		/*@ admit \valid(b+(0 .. N-1)); */
		/*@ admit \separated(a+(0 .. N-1), b+(0 .. N-1)); */	a[0] = 6;
	b[0] = 1;
	/*@
	  loop invariant 1 <= i <= N;
	  loop invariant \forall integer j; 0 <= j < i ==> a[j] == 6*(j+1);
	  loop assigns i, a[0 .. N-1];
	  loop variant N - i;
	*/
	for(i=1; i<N; i++)
	{
		a[i] = a[i-1] + 6;
	}
	/*@
	  loop invariant 1 <= i <= N;
	  loop invariant \forall integer j; 0 <= j < N ==> a[j] == 6*(j+1);
	  loop invariant \forall integer j; 0 <= j < i ==> b[j] == 3*j*j + 3*j + 1;
	  loop assigns i, b[0 .. N-1];
	  loop variant N - i;
	*/
	for(i=1; i<N; i++)
	{
		b[i] = b[i-1] + a[i-1];
	}
	/*@
	  loop invariant 0 <= i <= N;
	  loop invariant \forall integer j; 0 <= j < N ==> a[j] == 6*(j+1);
	  loop invariant \forall integer j; 0 <= j < N ==> b[j] == 3*j*j + 3*j + 1;
	  loop assigns i;
	  loop variant N - i;
	*/
	for(i=0; i<N; i++)
	{
		//@ assert(b[i] == 3*i*i + 3*i + 1);
	}
	return 1;
}
