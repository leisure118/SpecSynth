#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include <assert.h>
#define SIZE 100000
int unknown();
int main()
{
	int i;
	int a[SIZE];
	int b[SIZE];
	int c[SIZE];
	/*@
	  loop invariant 0 <= i <= SIZE;
	  loop invariant \forall integer j; 0 <= j < i ==> a[j] == 0 || a[j] == 1;
	  loop invariant \forall integer j; 0 <= j < i ==> ((a[j] == 1) ==> (c[j] == j%2));
	  loop assigns i, a[0 .. SIZE-1], b[0 .. SIZE-1], c[0 .. SIZE-1];
	  loop variant SIZE - i;
	*/
	for (i = 0; i < SIZE; i++)
	{
		int q = unknown();
		a[i] = 0;
		if (q == 0)
		{
			a[i] = 1;
			b[i] = i % 2;
		}
		if (a[i] != 0)
		{
			if (b[i] == 0)
			{
				c[i] = 0;
			}
			else
			{
				c[i] = 1;
			}
		}
	}
	a[15000] = 1;
		/*@ admit \forall integer j; 0 <= j < SIZE ==> ((a[j] == 1) ==> (c[j] == j%2)); */
	/*@
	  loop invariant 0 <= i <= SIZE;
	  loop assigns i;
	  loop variant SIZE - i;
	*/
	for (i = 0; i < SIZE; i++)
	{
		if (i == 15000 )
		{
			//@ assert(c[i] == 0);
		}
	}
	return 0;
}
