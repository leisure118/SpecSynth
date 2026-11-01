#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result <= 0;
*/
int unknown();
#include <assert.h>
#define SIZE 100000
int main()
{
    int array[SIZE];
    int i;
    int num = unknown();
		/*@
		  loop invariant 0 <= i;
		  loop invariant i <= num || num < 0;
		  loop invariant \forall integer j; 0 <= j < i ==> array[j] % 2 == j % 2;
		  loop assigns i, array[0 .. SIZE-1];
		  loop variant num - i;
		*/
		for(i = 0; i < num; i++)
		{
		  array[i] = unknown();
		  //@ assert array[i] % 2 == i % 2;
		}
    /*@
      loop invariant 0 <= i;
      loop invariant i <= num || num < 0;
      loop invariant \forall integer j; 0 <= j < num ==> array[j] % 2 == j % 2;
      loop assigns i;
      loop variant num - i;
    */
    for (i = 0; i < num; i++)
    {
        if (array[i] % 2 == 0)
        {
            //@ assert(  ( i % 2 ) == 0  );
        }
    }
    /*@
      loop invariant 0 <= i;
      loop invariant i <= num || num < 0;
      loop invariant \forall integer j; 0 <= j < num ==> array[j] % 2 == j % 2;
      loop assigns i;
      loop variant num - i;
    */
    for (i = 0; i < num; i++)
    {
        if (array[i] % 2 != 0)
        {
            //@ assert(  ( i % 2 ) != 0  );
        }
    }
  return 0;
}
