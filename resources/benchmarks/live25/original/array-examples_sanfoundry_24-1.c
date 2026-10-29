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
		for(i = 0; i < num; i++) 
		{
		  array[i] = unknown();
		}
    for (i = 0; i < num; i++)
    {
        if (array[i] % 2 == 0)
        {
            //@ assert(  ( i % 2 ) == 0  );
        }
    }
    for (i = 0; i < num; i++)
    {
        if (array[i] % 2 != 0)
        {
            //@ assert(  ( i % 2 ) != 0  );
        }
    }
  return 0;
}
