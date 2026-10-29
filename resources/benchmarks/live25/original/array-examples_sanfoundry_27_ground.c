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
    int i;
		for(i = 0; i < SIZE; i++) 
		{
		  array[i] = unknown();
		}
    int largest = array[0];
    for (i = 1; i < SIZE; i++)
    {
        if (largest < array[i])
            largest = array[i];
    }
    int x;
    for ( x = 0 ; x < SIZE ; x++ ) {
      //@ assert(largest >= array[ x ]  );
    }
    return 0;
}
