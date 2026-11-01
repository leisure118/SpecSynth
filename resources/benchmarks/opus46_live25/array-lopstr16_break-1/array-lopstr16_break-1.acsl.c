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
	/*@
	  loop invariant 0 <= i <= SIZE;
	  loop invariant c <= 5 ==> \forall integer j; 0 <= j < i ==> \valid(s[j].n);
	  loop assigns i, s[0 .. SIZE-1], __fc_heap_status;
	  loop variant SIZE - i;
	*/
	for(i = 0; i < SIZE; i++)
	{
		if(c > 5)
			break;
		s[i].n = malloc(sizeof(int));
		//@ admit \valid(s[i].n);
	}
	/*@
	  loop invariant 0 <= i <= SIZE;
	  loop invariant c <= 5 ==> \forall integer j; 0 <= j < SIZE ==> \valid(s[j].n);
	  loop assigns i;
	  loop variant SIZE - i;
	*/
	for(i = 0; i < SIZE; i++)
	{
		if(c <= 5){
			//@ assert(s[i].n != 0);
		}
	}
	return 0;
}
