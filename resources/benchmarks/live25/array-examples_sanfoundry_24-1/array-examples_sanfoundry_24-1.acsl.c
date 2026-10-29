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
    int num = unknown();
			/*@
			  loop invariant 0 <= i && (i <= num || num < 0);
			  loop assigns i, array[0 .. SIZE-1];
			  loop variant num - i;
			*/		for(i = 0; i < num; i++) 
		{
		  array[i] = unknown();
		}
    /*@
      loop invariant 0 <= i && (i <= num || num < 0);
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
      loop invariant 0 <= i && (i <= num || num < 0);
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
