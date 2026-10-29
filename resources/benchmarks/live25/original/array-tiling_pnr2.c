#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include<stdlib.h>
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
		if(SIZE % 2 != 0) { return 1; }
		//@ assert(SIZE % 2 == 0);
		for (i = 1 ; i <= SIZE/2 ; i++)
		{
			value = ReadFromPort();	
			if(value != DEFAULTVAL)
			{
				a[i*2 - 2] = value ;   
			}
			else 
			{
				a[i*2 - 2] = FIXEDVAL;  
			}
			value = ReadFromPort();	
			if(value != DEFAULTVAL)
			{
				a[i*2 - 1] = value ;   
			}
			else 
			{
				a[i*2 - 1] = FIXEDVAL;  
			}
		}
		for ( i = 0; i < SIZE; i++)  
		{
			//@ assert(a[i]!=DEFAULTVAL);
		}
	}
	return 1;
}
