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
	for(i=0; i<N; i++)
	{
		if(i==0) {
			a[0] = 2;
		} else {
			a[i] = a[i-1] + 2;
		}
	}
	for(i=0; i<N; i++)
	{
		if(i==0) {
			b[0] = 1;
		} else {
			b[i] = b[i-1] + a[i-1];
		}
	}
	for(i=0; i<N; i++)
	{
		//@ assert(b[i] == i*i + i + 1);
	}
	return 1;
}
