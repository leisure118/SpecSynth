#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include<stdlib.h>
#include <assert.h>
#define SIZE 100000
struct S
{
	int t;
	int * p1;
};
struct S* a[SIZE];
int main()
{
	int i;
	for(i = 0; i < SIZE; i = i+2)
	{
		struct S* s = (struct S*) malloc(sizeof(struct S));
		s->t = unknown();
		if (s->t == 10)
			s->p1 = (int *) malloc(sizeof(int));
		a[i] = s;
	}
	/*@
	  loop invariant 0 <= i <= SIZE;
	  loop invariant i % 2 == 0;
	  loop assigns i;
	  loop variant SIZE - i;
	*/
	for(i = 0; i < SIZE; i = i+2)
	{
		//@ admit \valid(a[i]);
		struct S* u = a[i];
		if (u->t == 10)
		{
			//@ admit \valid(u->p1);
			//@ assert(u->p1 != (void *) 0);
		}
	}
}
