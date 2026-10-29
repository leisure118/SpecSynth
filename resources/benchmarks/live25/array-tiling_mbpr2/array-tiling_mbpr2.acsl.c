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
		  loop invariant \forall integer j; 1 <= j < i ==> (CCCELVOL2 >= MINVAL ? volArray[2*j-2] == CCCELVOL2 : volArray[2*j-2] == 0);
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
		  loop invariant \forall integer j; 1 <= j < i ==> (CCCELVOL1 >= MINVAL ? volArray[2*j-1] == CCCELVOL1 : volArray[2*j-1] == 0);
		  loop invariant \forall integer j; 1 <= j <= CELLCOUNT/2 ==> (CCCELVOL2 >= MINVAL ? volArray[2*j-2] == CCCELVOL2 : volArray[2*j-2] == 0);
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
		//@ assert \forall integer j; 1 <= j <= CELLCOUNT/2 ==> (volArray[2*j-2] >= MINVAL || volArray[2*j-2] == 0);
		//@ assert \forall integer j; 1 <= j <= CELLCOUNT/2 ==> (volArray[2*j-1] >= MINVAL || volArray[2*j-1] == 0);
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
