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
		int tmp;
		int *a = malloc(sizeof(int)*SIZE);
		int *b = malloc(sizeof(int)*SIZE);
		int *a_copy = malloc(sizeof(int)*SIZE);
		int *b_copy = malloc(sizeof(int)*SIZE);
		for(i=0; i<SIZE; i++)
		{
			a_copy[i] = unknown();
			b_copy[i] = unknown();
		}
		for(i=0; i<SIZE; i++)
		{
			a[i] = a_copy[SIZE-i-1];
			b[i] = b_copy[SIZE-i-1];
		}
		for(i=0; i<SIZE; i++)
		{
			tmp = a[i];
			a[i] = b[i];
			b[i] = tmp;
		}
		for(i=0; i<SIZE; i++)
		{
			tmp = a[i];
			a[i] = b[i];
			b[i] = tmp;
		}
		for(i=0; i<SIZE; i++)
		{
			//@ assert(a[i] == a_copy[SIZE-i-1]);
		}
	}
	return 1;
}
