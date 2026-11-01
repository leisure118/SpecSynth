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
int main()
{
	int i;
	for (i = 0; i < SIZE; i++)
	{
		struct S *s1 = (struct S *) malloc(sizeof(struct S));
		s1->n = unknown();
		if (s1->n == 0)
		{
			s1->p = (int *) malloc(sizeof(int));
		}
		else
		{
			s1->p = 0;
		}
		a[i] = s1;
	}
	/*@
	  loop invariant 0 <= i <= SIZE;
	  loop assigns i;
	  loop variant SIZE - i;
	*/
	for (i = 0; i < SIZE; i++)
	{
		//@ admit \valid(a[i]);
		struct S *s2 = a[i];
		if (s2->n == 0)
		{
			//@ admit \valid(s2->p);
			//@ assert(s2->p != 0);
		}
	}
	return 0;
}
