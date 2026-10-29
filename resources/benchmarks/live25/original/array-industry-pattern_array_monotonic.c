#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include <assert.h>
#define SIZE 100000
int main()
{
	int i;
	int a[SIZE];
	int b[SIZE];
	for(i = 0; i < SIZE;  i = i + 2)
	{
		a[i] = unknown();
		if(a[i] == 10)
			b[i] = 20;
	}
	for(i = 0; i < SIZE; i = i + 2)
	{
		if(a[i] == 10){
			//@ assert(b[i] == 20);
		}
	}
}
