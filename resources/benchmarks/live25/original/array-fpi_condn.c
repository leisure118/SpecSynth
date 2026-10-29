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
	int *a = malloc(sizeof(int)*N);
	for(i=0; i<N; i++)
	{
		a[i] = unknown();
	}
	for(i=0; i<N; i++)
	{
		if(a[i] < N) {
			a[i] = a[i];
		} else {
			a[i] = N;
		}
	}
	for(i=0; i<N; i++)
	{
		//@ assert(a[i] <= N);
	}
	return 1;
}
