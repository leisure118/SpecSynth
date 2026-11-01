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
		int MINVAL;
		int i;
		int volArray[CELLCOUNT];
		int CCCELVOL3 = 7;
		int CCCELVOL2 = 3;
		int CCCELVOL1 = 1;
		if(CELLCOUNT % 3 != 0) { return 1; }
		//@ assert(CELLCOUNT % 3 == 0);
		/*@
		  loop invariant 1 <= i <= CELLCOUNT/3 + 1;
		  loop invariant \forall integer j; 0 <= j < 3*(i-1) ==> (volArray[j] >= MINVAL || volArray[j] == 0);
		  loop assigns i, volArray[0 .. CELLCOUNT-1];
		  loop variant CELLCOUNT/3 + 1 - i;
		*/
		for(i = 1; i <= CELLCOUNT/3; i++)
		{
			if(CCCELVOL3 >= MINVAL)
			{
				volArray[i*3 - 3] = CCCELVOL3;
			}
			else
			{
				volArray[i*3 - 3] = 0;
			}
			if(CCCELVOL2 >= MINVAL)
			{
				volArray[i*3 - 2] = CCCELVOL2;
			}
			else
			{
				volArray[i*3 - 2] = 0;
			}
			if(CCCELVOL1 >= MINVAL)
			{
				volArray[i*3 - 1] = CCCELVOL1;
			}
			else
			{
				volArray[i*3 - 1] = 0;
			}
		}
		/*@
		  loop invariant 0 <= i <= CELLCOUNT;
		  loop invariant \forall integer j; 0 <= j < CELLCOUNT ==> (volArray[j] >= MINVAL || volArray[j] == 0);
		  loop assigns i;
		  loop variant CELLCOUNT - i;
		*/
		for(i = 0; i < CELLCOUNT; i++)
		{
			//@ assert(volArray[i] >= MINVAL || volArray[i] == 0 );
		}
	}
	return 1;
}
