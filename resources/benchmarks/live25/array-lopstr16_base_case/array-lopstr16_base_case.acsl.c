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
	int n;
	int *p;
};
struct S *a[SIZE];
static struct S pool[SIZE];
static int p_pool[SIZE];
int main()
{
	int i;
	//@ admit \separated(a+(0 .. SIZE-1), pool+(0 .. SIZE-1), p_pool+(0 .. SIZE-1));
	//@ admit \valid(pool + (0 .. SIZE-1));
	//@ admit \valid(p_pool + (0 .. SIZE-1));
	/*@
	  loop invariant 0 <= i <= SIZE;
	  loop invariant \forall integer j; 0 <= j < i ==> a[j] == &pool[j];
	  loop invariant \forall integer j; 0 <= j < i ==> \valid(a[j]);
	  loop invariant \forall integer j; 0 <= j < i && a[j]->n == 0 ==> \valid(a[j]->p);
	  loop assigns i, a[0 .. SIZE-1], a[0 .. SIZE-1]->n, a[0 .. SIZE-1]->p;
	  loop variant SIZE - i;
	*/
	for (i = 0; i < SIZE; i++)
	{
		a[i] = &pool[i];
		a[i]->n = unknown();
		if (a[i]->n == 0)
		{
			a[i]->p = &p_pool[i];
		}
		else
		{
			a[i]->p = 0;
		}
	}
	/*@
	  loop invariant 0 <= i <= SIZE;
	  loop invariant \forall integer j; 0 <= j < SIZE ==> a[j] == &pool[j];
	  loop invariant \forall integer j; 0 <= j < SIZE ==> \valid(a[j]);
	  loop invariant \forall integer j; 0 <= j < SIZE && a[j]->n == 0 ==> \valid(a[j]->p);
	  loop assigns i;
	  loop variant SIZE - i;
	*/
	for (i = 0; i < SIZE; i++)
	{
		struct S *s2 = a[i];
		if (s2->n == 0)
		{
			//@ assert(s2->p != 0);
		}
	}
	return 0;
}
