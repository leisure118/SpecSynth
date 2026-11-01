#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include <assert.h>
#define SIZE 1000000
struct _S
{
	int n;
};
typedef struct _S S;
S a[SIZE];
S b[SIZE];
S c[SIZE];
int main()
{
	int i;
	/*@
	  loop invariant 0 <= i <= SIZE;
	  loop assigns i, a[0 .. SIZE-1], b[0 .. SIZE-1];
	  loop variant SIZE - i;
	*/
	for(i = 0; i < SIZE; i++)
	{
		int v;
	        v = unknown();
		a[i].n= v;
		v = unknown();
		b[i].n = v;
	}
	/*@
	  loop invariant 0 <= i <= SIZE;
	  loop invariant \forall integer j; 0 <= j < i ==> c[j].n == a[j].n + b[j].n;
	  loop assigns i, c[0 .. SIZE-1];
	  loop variant SIZE - i;
	*/
	for(i = 0; i < SIZE; i++)
	{
		c[i].n = a[i].n + b[i].n;
	}
	/*@
	  loop invariant 0 <= i <= SIZE;
	  loop invariant \forall integer j; 0 <= j < SIZE ==> c[j].n == a[j].n + b[j].n;
	  loop assigns i;
	  loop variant SIZE - i;
	*/
	for(i = 0; i < SIZE; i++)
	{
		//@ assert(c[i].n == a[i].n + b[i].n);
	}
	return 0;
}
