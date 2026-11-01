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
		int DEFAULTVALUE=1;
		int MINVAL=2;
		int i;
		int j;
		int volArray[CELLCOUNT];
		if(CELLCOUNT % 2 != 0) { return 1; }
		//@ assert(CELLCOUNT % 2 == 0);
		/*@
		  loop invariant 1 <= i <= CELLCOUNT/2 + 1;
		  loop invariant \forall integer k; 0 <= k < 2*(i-1) ==> (volArray[k] >= MINVAL || volArray[k] == 0);
		  loop assigns i, j, volArray[0 .. CELLCOUNT-1];
		  loop variant CELLCOUNT/2 + 1 - i;
		*/
		for(i = 1; i <= CELLCOUNT/2; i++)
		{
			/*@
			  loop invariant 0 <= j <= 2;
			  loop invariant j <= 1 ==> volArray[i*2-2] == 2;
			  loop invariant j == 0 ==> volArray[i*2-1] == 0;
			  loop invariant \forall integer k; 0 <= k < 2*(i-1) ==> (volArray[k] >= MINVAL || volArray[k] == 0);
			  loop assigns j, volArray[i*2-2 .. i*2-1];
			  loop variant j;
			*/
			for(j = 2; j >= 1; j--)
			{
				if(j >= MINVAL)
				{
					volArray[i*2 - j] = j;
				}
				else
				{
					volArray[i*2 - j] = 0;
				}
			}
		}
		/*@
		  loop invariant 0 <= i <= CELLCOUNT;
		  loop invariant \forall integer k; 0 <= k < CELLCOUNT ==> (volArray[k] >= MINVAL || volArray[k] == 0);
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
