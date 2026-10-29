#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include<stdlib.h>
int SIZE;
const int MAX = 100000;
int main()
{
	SIZE = unknown();
	if(SIZE > 1 && SIZE < MAX)
	{
		int i;
		int *a = malloc(sizeof(int)*SIZE);
		int *acopy = malloc(sizeof(int)*SIZE);
		//@ admit \valid(a+(0 .. SIZE-1));
		//@ admit \valid(acopy+(0 .. SIZE-1));
		//@ admit \separated(a+(0 .. SIZE-1), acopy+(0 .. SIZE-1));
		/*@
		  loop invariant 0 <= i <= SIZE;
		  loop assigns i, a[0 .. SIZE-1];
		  loop variant SIZE - i;
		*/
		for(i = 0; i < SIZE; i++)
		{
		    a[i] = unknown();
		}
		if(SIZE % 2 != 0) { return 1; }
		//@ assert(SIZE % 2 == 0);
		/*@
		  loop invariant 0 <= i <= SIZE/2;
		  loop invariant \forall integer j; 0 <= j < i ==> acopy[j] == a[j];
		  loop invariant \forall integer j; SIZE-i <= j < SIZE ==> acopy[j] == a[j];
		  loop assigns i, acopy[0 .. SIZE-1];
		  loop variant SIZE/2 - i;
		*/
		for(i=0; i<SIZE/2; i++)
		{
			acopy[SIZE-i-1] = a[SIZE-i-1];
			acopy[i] = a[i];
		}
		/*@
		  loop invariant 0 <= i <= SIZE;
		  loop invariant \forall integer j; 0 <= j < SIZE ==> acopy[j] == a[j];
		  loop assigns i;
		  loop variant SIZE - i;
		*/
		for(i=0; i<SIZE; i++)
		{
			//@ assert(acopy[i] == a[i]);
		}
	}
	return 1;
}
