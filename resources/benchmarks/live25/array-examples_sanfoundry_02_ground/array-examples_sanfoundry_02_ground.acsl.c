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
		/*@
		  loop invariant 0 <= i <= MAX;
		  loop assigns i, array[0 .. MAX-1];
		  loop variant MAX - i;
		*/
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
    /*@
      loop invariant 2 <= i <= MAX;
      loop invariant \forall integer j; 0 <= j < i ==> array[j] <= largest1;
      loop invariant largest2 <= largest1;
      loop invariant \forall integer j; 0 <= j < i ==> (array[j] <= largest2 || array[j] == largest1);
      loop assigns i, largest1, largest2;
      loop variant MAX - i;
    */
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
    /*@
      loop invariant 0 <= x <= MAX;
      loop invariant \forall integer j; 0 <= j < MAX ==> array[j] <= largest1;
      loop assigns x;
      loop variant MAX - x;
    */
    for( x = 0 ; x < MAX ; x++ ) {
      //@ assert(array[ x ] <= largest1  );
    }
    /*@
      loop invariant 0 <= x <= MAX;
      loop invariant \forall integer j; 0 <= j < MAX ==> (array[j] <= largest2 || array[j] == largest1);
      loop assigns x;
      loop variant MAX - x;
    */
    for( x = 0 ; x < MAX ; x++ ) {
      //@ assert(array[x] <= largest2 || array[x] == largest1  );
    }
  return 0;
}
