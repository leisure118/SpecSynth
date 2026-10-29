#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include<stdlib.h>
#include <assert.h>
#define SIZE 1000000
struct S
{
	int *n;
};
struct S s[SIZE];
int main()
{
	int i;
	int c=unknown();
	for(i = 0; i < SIZE; i++)
	{
		if(c > 5)
			break;
		s[i].n = malloc(sizeof(int));
	}
	for(i = 0; i < SIZE; i++)
	{
		if(c <= 5){
			//@ assert(s[i].n != 0);
		}
	}
	return 0;
}
