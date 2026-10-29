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
	int *p;
	int n;
};
struct S *a[SIZE];
int main()
{
	int i;
	for (i = 0; i < SIZE; i++)
	{
		int q = unknown();
		struct S *s = 0;
		if (q == 0)
		{
			s = (struct S*) malloc(sizeof(struct S));
			s->n = q % 2;
		}
		if (s != 0)
		{
			if (s->n == 0)
			{
				s->p = (int *) malloc(sizeof(int));
			}
			else
			{
				s->p = 0;
			}
		}
		a[i] = s;
	}
	a[3] = (struct S*) malloc(sizeof(struct S));
	for (i = 0; i < SIZE; i++)
	{
		struct S *s1 = a[i];
		if (i != 3 && s1 != 0 && s1->n == 0)
		{
			//@ assert(s1->p != 0); 
		}
	}
	return 0;
}
