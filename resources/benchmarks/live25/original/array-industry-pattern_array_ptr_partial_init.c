#include<stdlib.h>
#include <assert.h>
#define SIZE 100000
int *a[SIZE];
int i;
int main ()
{
	for(i = 0; i < SIZE; i++)
	{
		a[i] = 0;
	}
	for(i = 0; i < SIZE / 2; i++)
	{
		a[i] = malloc(sizeof(int)) ;
	}
	for(i = 0; i < SIZE / 2; i++)
	{
		//@ assert(a[i] != 0);
	}
return 0;
}	
