#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
int CELLCOUNT;
int main()
{
	CELLCOUNT = unknown();
	if(CELLCOUNT > 1)
	{
		int MINVAL=2;
		int i;
		int volArray[CELLCOUNT];
		int CCCELVOL2 = 3;
		int CCCELVOL1 = 1;
		if(CELLCOUNT % 2 != 0) { return 1; }
		//@ assert(CELLCOUNT % 2 == 0);
		/*@
		  loop invariant 1 <= i <= CELLCOUNT/2 + 1;
		  loop invariant \forall integer k; 1 <= k < i ==> (volArray[k*2 - 2] >= MINVAL || volArray[k*2 - 2] == 0);
		  loop assigns i, volArray[0 .. CELLCOUNT-1];
		  loop variant CELLCOUNT/2 + 1 - i;
		*/
		for(i = 1; i <= CELLCOUNT/2; i++)
		{
			if(CCCELVOL2 >= MINVAL)
			{
				volArray[i*2 - 2] = CCCELVOL2;
			}
			else
			{
				volArray[i*2 - 2] = 0;
			}
			volArray[i*2 - 1] = volArray[i*2 - 1];
		}
		/*@
		  loop invariant 1 <= i <= CELLCOUNT/2 + 1;
		  loop invariant \forall integer k; 1 <= k <= CELLCOUNT/2 ==> (volArray[k*2 - 2] >= MINVAL || volArray[k*2 - 2] == 0);
		  loop invariant \forall integer k; 1 <= k < i ==> (volArray[k*2 - 1] >= MINVAL || volArray[k*2 - 1] == 0);
		  loop assigns i, volArray[0 .. CELLCOUNT-1];
		  loop variant CELLCOUNT/2 + 1 - i;
		*/
		for(i = 1; i <= CELLCOUNT/2; i++)
		{
			if(CCCELVOL1 >= MINVAL)
			{
				volArray[i*2 - 1] = CCCELVOL1;
			}
			else
			{
				volArray[i*2 - 1] = 0;
			}
			volArray[i*2 - 2] = volArray[i*2 - 2];
		}
		/*@
		  loop invariant 0 <= i <= CELLCOUNT;
		  loop invariant \forall integer k; 1 <= k <= CELLCOUNT/2 ==> (volArray[k*2 - 2] >= MINVAL || volArray[k*2 - 2] == 0);
		  loop invariant \forall integer k; 1 <= k <= CELLCOUNT/2 ==> (volArray[k*2 - 1] >= MINVAL || volArray[k*2 - 1] == 0);
		  loop assigns i;
		  loop variant CELLCOUNT - i;
		*/
		for(i = 0; i < CELLCOUNT; i++)
		{
			//@ assert 0 <= i < CELLCOUNT && CELLCOUNT % 2 == 0;
			//@ assert i % 2 == 0 ==> 1 <= i/2 + 1 <= CELLCOUNT/2;
			//@ assert i % 2 == 0 ==> (i/2 + 1)*2 - 2 == i;
			//@ assert i % 2 != 0 ==> 1 <= (i + 1)/2 <= CELLCOUNT/2;
			//@ assert i % 2 != 0 ==> ((i + 1)/2)*2 - 1 == i;
			//@ assert(volArray[i] >= MINVAL || volArray[i] == 0 );
		}
	}
	return 1;
}
