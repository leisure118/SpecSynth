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
/*@
  requires size >= 0;
  requires \valid(a+(0 .. size-1));
  assigns a[0 .. size-1];
*/
void init(S a[], int size)
{
	int i;
	/*@
	  loop invariant 0 <= i <= size;
	  loop assigns i, a[0 .. size-1];
	  loop variant size - i;
	*/
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
		//@ assert(a[i].n == 0 );
		}
	}
	return 0;
}	
