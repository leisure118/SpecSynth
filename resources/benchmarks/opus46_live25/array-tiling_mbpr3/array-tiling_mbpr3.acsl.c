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
		int CCCELVOL3 = 7;
		int CCCELVOL2 = 3;
		int CCCELVOL1 = 1;
		if(CELLCOUNT %3 != 0) { return 1; }
		//@ assert(CELLCOUNT % 3 == 0);
		/*@
		  loop invariant 1 <= i <= CELLCOUNT/3 + 1;
		  loop invariant \forall integer j; 0 <= j < 3*(i-1) && j % 3 == 0 ==> volArray[j] == CCCELVOL3;
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
			volArray[i*3 - 2] = volArray[i*3 - 2];
			volArray[i*3 - 1] = volArray[i*3 - 1];
		}
		/*@
		  loop invariant 1 <= i <= CELLCOUNT/3 + 1;
		  loop invariant \forall integer j; 0 <= j < CELLCOUNT && j % 3 == 0 ==> volArray[j] == CCCELVOL3;
		  loop invariant \forall integer j; 0 <= j < 3*(i-1) && j % 3 == 1 ==> volArray[j] == CCCELVOL2;
		  loop assigns i, volArray[0 .. CELLCOUNT-1];
		  loop variant CELLCOUNT/3 + 1 - i;
		*/
		for(i = 1; i <= CELLCOUNT/3; i++)
		{
			if(CCCELVOL2 >= MINVAL)
			{
				volArray[i*3 - 2] = CCCELVOL2;
			}
			else
			{
				volArray[i*3 - 2] = 0;
			}
			volArray[i*3 - 3] = volArray[i*3 - 3];
			volArray[i*3 - 1] = volArray[i*3 - 1];
		}
		/*@
		  loop invariant 1 <= i <= CELLCOUNT/3 + 1;
		  loop invariant \forall integer j; 0 <= j < CELLCOUNT && j % 3 == 0 ==> volArray[j] == CCCELVOL3;
		  loop invariant \forall integer j; 0 <= j < CELLCOUNT && j % 3 == 1 ==> volArray[j] == CCCELVOL2;
		  loop invariant \forall integer j; 0 <= j < 3*(i-1) && j % 3 == 2 ==> volArray[j] == 0;
		  loop assigns i, volArray[0 .. CELLCOUNT-1];
		  loop variant CELLCOUNT/3 + 1 - i;
		*/
		for(i = 1; i <= CELLCOUNT/3; i++)
		{
			if(CCCELVOL1 >= MINVAL)
			{
				volArray[i*3 - 1] = CCCELVOL1;
			}
			else
			{
				volArray[i*3 - 1] = 0;
			}
			volArray[i*3 - 2] = volArray[i*3 - 2];
			volArray[i*3 - 3] = volArray[i*3 - 3];
		}
		/*@
		  loop invariant 0 <= i <= CELLCOUNT;
		  loop invariant \forall integer j; 0 <= j < CELLCOUNT && j % 3 == 0 ==> volArray[j] == CCCELVOL3;
		  loop invariant \forall integer j; 0 <= j < CELLCOUNT && j % 3 == 1 ==> volArray[j] == CCCELVOL2;
		  loop invariant \forall integer j; 0 <= j < CELLCOUNT && j % 3 == 2 ==> volArray[j] == 0;
		  loop invariant CCCELVOL3 >= MINVAL;
		  loop invariant CCCELVOL2 >= MINVAL;
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
