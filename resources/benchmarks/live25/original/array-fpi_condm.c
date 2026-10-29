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
	for (i = 0; i < N; i++)
	{
		a[i] = 0;
	}
	for (i = 0; i < N; i++)
	{
		if (N%2 == 0) {
			a[i] = a[i] + 2;
		} else {
			a[i] = a[i] + 1;
		}
	}
	for (i = 0; i < N; i++)
	{
		//@ assert(a[i] % 2 == N % 2);
	}
	return 1;
}
