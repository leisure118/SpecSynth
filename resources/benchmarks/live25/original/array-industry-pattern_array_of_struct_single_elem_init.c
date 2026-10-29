#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include <assert.h>
#define SIZE 100000
struct S
{
	int p;
	int n;
};
struct S a[SIZE];
int main()
{
	int i;
	for (i = 0; i < SIZE; i++)
	{
		int q = unknown();
		struct S s;
	  s.n = unknown();
		if (s.n == 0)
		{
		    s.p =10 ;
		}
		else
		{
	 		s.p = 20;
		}
		a[i] = s;
	}
	a[3].p = 30;
	a[3].n = 40;
	for (i = 0; i < SIZE; i++)
	{
		struct S s1 = a[i];
		if (i != 3 && s1.n == 0)
		{
			//@ assert(s1.p == 10); 
		}
	}
	return 0;
}
