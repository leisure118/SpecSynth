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
		int j;
		int volArray[CELLCOUNT];
		if(CELLCOUNT % 3 != 0) { return 1; }
		//@ assert(CELLCOUNT % 3 == 0);
		for(i = 1; i <= CELLCOUNT/3; i++)
		{
			for(j = 3; j >= 1; j--)
			{
				if(j >= MINVAL)
				{
					volArray[i*3 - j] = j;
				}
				else
				{
					volArray[i*3 - j] = 0;
				}
			}
		}
		for(i = 0; i < CELLCOUNT; i++)
		{
			//@ assert(volArray[i] >= MINVAL || volArray[i] == 0 );
		}
	}
	return 1;
}
