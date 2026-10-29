#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include<stdlib.h>
/*@
  assigns \nothing;
*/
int ReadFromPort()
{
	int x = unknown();
	return x;
}
int SIZE;
const int MAX = 100000;
int main()
{
	SIZE = unknown();
	if(SIZE > 1 && SIZE < MAX)
	{
		int i;
		int value;
		int *a = malloc(sizeof(int)*SIZE);
		int DEFAULTVAL = 0;
		int FIXEDVAL = 10;
		//@ admit \valid(a+(0 .. SIZE-1));
		if(SIZE % 3 != 0) { return 1; }
		//@ assert(SIZE % 3 == 0);
		/*@
		  loop invariant 1 <= i <= SIZE/3 + 1;
		  loop invariant \forall integer j; 0 <= j < 3*(i-1) ==> a[j] != DEFAULTVAL;
		  loop assigns i, value, a[0 .. SIZE-1];
		  loop variant SIZE/3 + 1 - i;
		*/
		for (i = 1 ; i <= SIZE/3 ; i++)
		{
			value = ReadFromPort();
			if(value != DEFAULTVAL)
			{
				a[i*3 - 3] = value ;
			}
			else
			{
				a[i*3 - 3] = FIXEDVAL;
			}
			value = ReadFromPort();
			if(value != DEFAULTVAL)
			{
				a[i*3 - 2] = value ;
			}
			else
			{
				a[i*3 - 2] = FIXEDVAL;
			}
			value = ReadFromPort();
			if(value != DEFAULTVAL)
			{
				a[i*3 - 1] = value ;
			}
			else
			{
				a[i*3 - 1] = FIXEDVAL;
			}
		}
		/*@
		  loop invariant 0 <= i <= SIZE;
		  loop invariant \forall integer j; 0 <= j < SIZE ==> a[j] != DEFAULTVAL;
		  loop assigns i;
		  loop variant SIZE - i;
		*/
		for ( i = 0; i < SIZE; i++)
		{
			//@ assert(a[i]!=DEFAULTVAL);
		}
	}
	return 1;
}
