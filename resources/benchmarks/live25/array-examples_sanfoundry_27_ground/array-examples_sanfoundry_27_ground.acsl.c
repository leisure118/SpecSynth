#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include <assert.h>
#define SIZE 100000
int main()
{
    int array[SIZE];
    //@ admit \valid(array+(0 .. SIZE-1));
    int i;
	/*@
	  loop invariant 0 <= i <= SIZE;
	  loop invariant \forall integer j; 0 <= j < i ==> INT_MIN <= array[j] < INT_MAX;
	  loop assigns i, array[0 .. SIZE-1];
	  loop variant SIZE - i;
	*/
	for(i = 0; i < SIZE; i++)
	{
	  array[i] = unknown();
	}
    int largest = array[0];
    /*@
      loop invariant 1 <= i <= SIZE;
      loop invariant \forall integer j; 0 <= j < i ==> largest >= array[j];
      loop assigns i, largest;
      loop variant SIZE - i;
    */
    for (i = 1; i < SIZE; i++)
    {
        if (largest < array[i])
            largest = array[i];
    }
    int x;
    /*@
      loop invariant 0 <= x <= SIZE;
      loop invariant \forall integer j; 0 <= j < SIZE ==> largest >= array[j];
      loop assigns x;
      loop variant SIZE - x;
    */
    for ( x = 0 ; x < SIZE ; x++ ) {
      //@ assert(largest >= array[ x ]  );
    }
    return 0;
}
