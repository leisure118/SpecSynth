#include<stdlib.h>
/*@
	assigns \nothing;
	ensures 1 < \result < 100000;
*/
int unknown();
long SIZE;
const int MAX = 100000;
int main()
{
	SIZE = unknown();
	if(SIZE > 1 && SIZE < MAX)
	{
		int i;
		long *a = malloc(sizeof(long)*SIZE);
		long long sum=0;
		/*@
		  loop invariant 0 <= i <= SIZE;
		  loop invariant \forall integer j; 0 <= j < i ==> a[j] == 1;
		  loop assigns i, a[0 .. SIZE-1];
		  loop variant SIZE - i;
		*/
		for(i = 0; i < SIZE; i++ )
		{
			a[i] = 1;
		}
		/*@
		  loop invariant 0 <= i <= SIZE;
		  loop invariant \forall integer j; 0 <= j < SIZE ==> a[j] == 1;
		  loop invariant sum == i;
		  loop assigns i, sum;
		  loop variant SIZE - i;
		*/
		for(i = 0; i < SIZE; i++ )
		{
			sum = sum + a[i];
		}
		/*@
		  loop invariant 0 <= i <= SIZE;
		  loop invariant \forall integer j; 0 <= j < SIZE ==> a[j] == 1;
		  loop invariant sum == SIZE + i;
		  loop assigns i, sum;
		  loop variant SIZE - i;
		*/
		for(i = 0; i < SIZE; i++ )
		{
			sum = sum + a[i];
		}
		/*@
		  loop invariant 0 <= i <= SIZE;
		  loop invariant \forall integer j; 0 <= j < SIZE ==> a[j] == 1;
		  loop invariant sum == 2*SIZE - i;
		  loop assigns i, sum;
		  loop variant SIZE - i;
		*/
		for(i = 0; i < SIZE; i++)
		{
			sum = sum - a[i];
		}
		/*@
		  loop invariant 0 <= i <= SIZE;
		  loop invariant \forall integer j; 0 <= j < SIZE ==> a[j] == 1;
		  loop invariant sum == SIZE - i;
		  loop assigns i, sum;
		  loop variant SIZE - i;
		*/
		for(i = 0; i < SIZE; i++)
		{
			sum = sum - a[i];
		}
		//@ assert(sum == 0);
	}
	return 1;
}
