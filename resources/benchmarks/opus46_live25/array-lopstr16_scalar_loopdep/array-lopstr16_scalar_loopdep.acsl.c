#include <assert.h>
#define SIZE 100000
struct _S
{
	int n;
};
typedef struct _S S;
S a[SIZE];
int main()
{
	int i,x;
	int y = 100;
	/*@
	  loop invariant 0 <= i <= SIZE;
	  loop invariant y == 100 + i;
	  loop invariant \forall integer j; 0 <= j < i ==> a[j].n == 100 + j;
	  loop assigns i, x, y, a[0 .. SIZE-1];
	  loop variant SIZE - i;
	*/
	for(i = 0; i < SIZE; i++)
	{
		x = y;
		a[i].n = y;
		y++;
	}
	/*@
	  loop invariant 0 <= i <= SIZE;
	  loop invariant \forall integer j; 0 <= j < SIZE ==> a[j].n == 100 + j;
	  loop assigns i;
	  loop variant SIZE - i;
	*/
	for(i = 0; i < SIZE; i++)
	{
		//@ assert(a[i].n >= 100);
	}
	return 0;
}
