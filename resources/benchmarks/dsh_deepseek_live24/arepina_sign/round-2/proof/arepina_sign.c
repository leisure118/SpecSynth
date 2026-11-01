/*@
  requires \true;
  assigns \nothing;
  ensures (x > 0) ==> \result == 1;
  ensures (x < 0) ==> \result == -1;
  ensures (x == 0) ==> \result == 0;
  ensures \result == -1 || \result == 0 || \result == 1;
*/
int spec_sign(int x)
{
   return (x > 0) - (x < 0);
}
#ifdef OUT_OF_TASK
#include <stdio.h>
/*@
  assigns \nothing;
*/
int main(void)
{
   int a = spec_sign(10);
   //@ assert a == 1;
   int b = spec_sign(0);
   //@ assert b == 0;
}
#endif
