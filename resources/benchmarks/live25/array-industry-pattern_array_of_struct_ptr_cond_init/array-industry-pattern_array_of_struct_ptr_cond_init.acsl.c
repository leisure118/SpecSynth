#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include<stdlib.h>
#include <assert.h>
#define SIZE 100000
struct _S
{
	int *p;
	int n;
};
typedef struct _S S;
S *a[SIZE];
int user_read()
{
	int x = unknown();
	return x;
}
int main()
{
	int i;
	/*@
	  loop invariant 0 <= i <= SIZE;
	  loop invariant \forall integer j; 0 <= j < i ==> \valid(a[j]);
	  loop invariant \forall integer j; 0 <= j < i ==> (a[j]->n == 1 ==> a[j]->p != \null);
	  loop assigns i, a[0 .. SIZE-1];
	  loop variant SIZE - i;
	*/
	for(i = 0; i < SIZE; i++)
	{
		S *s1 = malloc(sizeof(S));
		//@ admit \valid(s1 + (0 .. 0));
		//@ admit \separated(s1, a + (0 .. SIZE-1));
		s1 -> n = user_read();
		if(s1 ->n == 1)
		{
			s1 -> p = malloc(sizeof(int));
			//@ admit \valid(s1->p + (0 .. 0));
		}
		else
		{
			s1 -> p = (void *)0;
		}
		a[i] = s1;
	}
	/*@
	  loop invariant 0 <= i <= SIZE;
	  loop invariant \forall integer j; 0 <= j < SIZE ==> \valid(a[j]);
	  loop invariant \forall integer j; 0 <= j < SIZE ==> (a[j]->n == 1 ==> a[j]->p != \null);
	  loop assigns i;
	  loop variant SIZE - i;
	*/
	for(i = 0; i < SIZE; i++)
	{
		S *s2 = a[i];
		if(s2 ->n == 1)
		{
			//@assert(s2 -> p != (void *)0);
		}
	}
	return 0;
}
