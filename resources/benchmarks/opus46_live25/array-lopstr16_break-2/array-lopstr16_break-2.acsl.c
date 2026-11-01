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
	  loop invariant 0 <= i <= 1000000;
	  loop invariant \forall integer j; 0 <= j < i ==> s[j].n == 10;
	  loop assigns i, s[0 .. 500000].n;
	  loop variant 1000000 - i;
	*/
	for(i = 0; i < SIZE; i++)
	{
		if(i > SIZE / 2)
			break;
		s[i].n = 10;
	}
	/*@
	  loop invariant 0 <= i <= 1000000;
	  loop invariant \forall integer j; 0 <= j <= 500000 ==> s[j].n == 10;
	  loop assigns i;
	  loop variant 1000000 - i;
	*/
	for(i = 0; i < SIZE; i++)
	{
		if(i <= SIZE /2 ){
			//@ assert(s[i].n == 10);
		}
	}
	return 0;
}
