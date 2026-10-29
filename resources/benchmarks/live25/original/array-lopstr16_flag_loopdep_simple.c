#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include <assert.h>
#define SIZE 1000000
typedef struct
{
	int n;
}S;
void init(S a[], int size)
{
	int i;
	for(i = 0; i < size; i++)
	{
		a[i].n = unknown();
	}
}
int main()
{
	S a[SIZE];
	int i;
	int flag;
	flag = 0;
	init(a, SIZE);
	for(i = 0; i < SIZE; i++)
	{
		if(a[i].n != 0)
		{
			flag = 1;
		}
	}
	for(i = 0; i < SIZE; i++)
	{
		if (flag == 0){
		//@ assert(a[i].n == 0 );
		}
	}
	return 0;
}	
