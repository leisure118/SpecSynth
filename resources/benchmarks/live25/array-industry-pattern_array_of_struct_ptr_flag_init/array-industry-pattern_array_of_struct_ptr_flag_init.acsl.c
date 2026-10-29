#include<stdlib.h>
#include <assert.h>
#define SIZE 100000
typedef struct
{
	int *n;
}S;
/*@
  requires \valid(a + (0 .. size-1));
  requires size >= 0;
  assigns a[0 .. size-1].n;
*/
void init(S a[], int size)
{
	//@ admit \false;
	int i;
	for(i = 0; i < size; i++)
	{
		a[i].n = (int *) malloc(sizeof(int));
	}
}
int main()
{
	S a[SIZE];
	int i;
	int flag;
	flag = 0;
	init(a, SIZE);
	/*@
	  loop invariant 0 <= i <= SIZE;
	  loop invariant (flag == 0) ==> (\forall integer j; 0 <= j < i ==> a[j].n == 0);
	  loop assigns i, flag;
	  loop variant SIZE - i;
	*/
	for(i = 0; i < SIZE; i++)
	{
		if(a[i].n != 0)
		{
			flag = 1;
		}
	}
	/*@
	  loop invariant 0 <= i <= SIZE;
	  loop invariant (flag == 0) ==> (\forall integer j; 0 <= j < SIZE ==> a[j].n == 0);
	  loop assigns i;
	  loop variant SIZE - i;
	*/
	for(i = 0; i < SIZE; i++)
	{
		if (flag == 0){
		//@ assert(a[i].n == 0);
		}
	}
	return 0;
}	
