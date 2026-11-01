/*@
  ensures x > 0 ==> \result == 1;
  ensures x < 0 ==> \result == -1;
  ensures x == 0 ==> \result == 0;
  assigns \nothing;
*/
int spec_sign(int x)
{
   return (x > 0) - (x < 0);
}
#ifdef OUT_OF_TASK
#include <stdio.h>
int main(void)
{
   int a = spec_sign(10);
   //@ assert a == 1;
   int b = spec_sign(0);
   //@ assert b == 0;
}
#endif
