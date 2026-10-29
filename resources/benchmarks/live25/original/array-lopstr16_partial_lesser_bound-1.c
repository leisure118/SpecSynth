#include <assert.h>
#define SIZE 10000000
int a[SIZE];
int i;
int main()
{
	for(i=0;i<SIZE;i++)
	{
	a[i] = 0 ;
	}
	for(i=0;i<SIZE/2;i++)
	{
	a[i] = 10 ;
	}
	for(i=0;i<SIZE/2;i++)
	{
		//@ assert(a[i]==10);
	}
	return 0;
}	
