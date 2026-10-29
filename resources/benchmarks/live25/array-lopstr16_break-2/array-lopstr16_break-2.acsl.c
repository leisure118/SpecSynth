#include <assert.h>
#define SIZE 1000000
struct S
{
	int n;
};
struct S s[SIZE];
int main()
{
	int i;
	/*@
	  loop invariant 0 <= i <= SIZE;
	  loop invariant \forall integer j; 0 <= j < i && j <= SIZE/2 ==> s[j].n == 10;
	  loop assigns i, s[0 .. SIZE-1];
	  loop variant SIZE - i;
	*/
	for(i = 0; i < SIZE; i++)
	{
		if(i > SIZE / 2)
			break;
		s[i].n = 10;
	}
	/*@
	  loop invariant 0 <= i <= SIZE;
	  loop invariant \forall integer j; 0 <= j < SIZE && j <= SIZE/2 ==> s[j].n == 10;
	  loop assigns i;
	  loop variant SIZE - i;
	*/
	for(i = 0; i < SIZE; i++)
	{
		if(i <= SIZE /2 ){
			//@ assert(s[i].n == 10);
		}
	}
	return 0;
}
