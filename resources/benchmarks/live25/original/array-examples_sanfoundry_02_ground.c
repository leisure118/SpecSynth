#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include <assert.h>
#define MAX 100000 
int main()
{
    int array[MAX];
    int i;
    int largest1;
    int largest2;
    int temp;
		for(i = 0; i < MAX; i++) 
		{
		  array[i] = unknown();
		}
    largest1 = array[0];
    largest2 = array[1];
    if (largest1 < largest2)
    {
        temp = largest1;
        largest1 = largest2;
        largest2 = temp;
    }
    for (i = 2; i < MAX;  i++)
    {
        if (array[i] >= largest1)
        {
            largest2 = largest1;
            largest1 = array[i];
        }
        else if (array[i] > largest2)
        {
            largest2 = array[i];
        }
    }
    int x;
    for( x = 0 ; x < MAX ; x++ ) {
      //@ assert(array[ x ] <= largest1  );
    }
    for( x = 0 ; x < MAX ; x++ ) {
      //@ assert(array[x] <= largest2 || array[x] == largest1  );
    }
  return 0;
}
