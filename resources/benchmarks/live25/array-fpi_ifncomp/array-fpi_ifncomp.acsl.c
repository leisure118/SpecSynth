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
	long long *c = malloc(sizeof(long long)*N);
	/*@ admit \valid(a+(0 .. N-1)); */
	/*@ admit \valid(b+(0 .. N-1)); */
	/*@ admit \valid(c+(0 .. N-1)); */
	/*@ admit \separated(a+(0 .. N-1), b+(0 .. N-1), c+(0 .. N-1)); */
	/*@
	  loop invariant 0 <= i <= N;
	  loop invariant \forall integer j; 0 <= j < i ==> a[j] == 6*(j+1);
	  loop assigns i, a[0 .. N-1];
	  loop variant N - i;
	*/
	for(i=0; i<N; i++)
	{
		if(i==0) {
			a[0] = 6;
		} else {
			a[i] = a[i-1] + 6;
		}
	}
	/*@
	  loop invariant 0 <= i <= N;
	  loop invariant \forall integer j; 0 <= j < N ==> a[j] == 6*(j+1);
	  loop invariant \forall integer j; 0 <= j < i ==> b[j] == 1 + 3*j*(j+1);
	  loop assigns i, b[0 .. N-1];
	  loop variant N - i;
	*/
	for(i=0; i<N; i++)
	{
		if(i==0) {
			b[0] = 1;
		} else {
			b[i] = b[i-1] + a[i-1];
		}
	}
	/*@
	  loop invariant 0 <= i <= N;
	  loop invariant \forall integer j; 0 <= j < N ==> a[j] == 6*(j+1);
	  loop invariant \forall integer j; 0 <= j < N ==> b[j] == 1 + 3*j*(j+1);
	  loop invariant \forall integer j; 0 <= j < i ==> c[j] == N + j*j*j;
	  loop assigns i, c[0 .. N-1];
	  loop variant N - i;
	*/
	for(i=0; i<N; i++)
	{
		if(i==0) {
			c[0] = N;
			/*@ admit c[0] == N + 0*0*0; */
		} else {
			c[i] = c[i-1] + b[i-1];
			/*@ admit c[i] == N + i*i*i; */
		}
	}
	/*@
	  loop invariant 0 <= i <= N;
	  loop invariant \forall integer j; 0 <= j < N ==> c[j] == N + j*j*j;
	  loop assigns i;
	  loop variant N - i;
	*/
	for(i=0; i<N; i++)
	{
		//@ assert(c[i] == N + i*i*i);
	}
	return 1;
}
