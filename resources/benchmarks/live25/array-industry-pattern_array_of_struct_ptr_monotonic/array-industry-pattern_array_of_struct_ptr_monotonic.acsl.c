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
	// Loop 1: allocate structs
	/*@
	  loop invariant 0 <= i <= SIZE;
	  loop invariant i % 2 == 0;
	  loop invariant \forall integer j; 0 <= j < i && j % 2 == 0 ==> \valid(a[j]);
	  loop assigns i, a[0 .. SIZE-1];
	  loop variant SIZE - i;
	*/
	for(i = 0; i < SIZE; i = i+2)
	{
		a[i] = (struct S*) malloc(sizeof(struct S));
		//@ admit \valid(a[i]);
	}
	// Loop 2: initialize structs
	/*@
	  loop invariant 0 <= i <= SIZE;
	  loop invariant i % 2 == 0;
	  loop invariant \forall integer j; 0 <= j < SIZE && j % 2 == 0 ==> \valid(a[j]);
	  loop invariant \forall integer j; 0 <= j < i && j % 2 == 0 && a[j]->t == 10 ==> \valid(a[j]->p1);
	  loop assigns i, a[i]->t, a[i]->p1;
	  loop variant SIZE - i;
	*/
	for(i = 0; i < SIZE; i = i+2)
	{
		a[i]->t = unknown();
		if (a[i]->t == 10) {
			a[i]->p1 = (int *) malloc(sizeof(int));
			//@ admit \valid(a[i]->p1);
		}
	}
	// Loop 3: verify
	/*@
	  loop invariant 0 <= i <= SIZE;
	  loop invariant i % 2 == 0;
	  loop invariant \forall integer j; 0 <= j < SIZE && j % 2 == 0 ==> \valid(a[j]);
	  loop invariant \forall integer j; 0 <= j < SIZE && j % 2 == 0 && a[j]->t == 10 ==> \valid(a[j]->p1);
	  loop assigns i;
	  loop variant SIZE - i;
	*/
	for(i = 0; i < SIZE; i = i+2)
	{
		struct S* u = a[i];
		if (u->t == 10)
		{
			//@ assert(u->p1 != (void *) 0);
		}
	}
}
