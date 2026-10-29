#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include <assert.h>
#define SIZE 100000
struct S
{
	int n;
};
struct S s[SIZE];
int main()
{
	int i;
	int c;
	c = unknown();
	/*@
	  loop invariant 0 <= i <= SIZE;
	  loop invariant \forall integer j; 0 <= j < i ==> s[j].n == 10;
	  loop assigns i, s[0 .. SIZE-1];
	  loop variant SIZE - i;
	*/
	for(i = 0; i < SIZE; i++)
	{
		if(c > 5)
			break;
		s[i].n = 10;
	}
	/*@
	  loop invariant 0 <= i <= SIZE;
	  loop invariant (c <= 5) ==> (\forall integer j; 0 <= j < SIZE ==> s[j].n == 10);
	  loop assigns i;
	  loop variant SIZE - i;
	*/
	for(i = 0; i < SIZE; i++)
	{
		if(c <= 5){
			//@ assert(s[i].n == 10);
		}
	}
	return 0;
}
