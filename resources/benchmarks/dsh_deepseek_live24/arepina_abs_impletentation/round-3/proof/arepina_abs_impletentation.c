#define SPEC_INT_MIN -2147483648
#define SPEC_INT_MAX 2147483647
/*@
  assigns \nothing;
  ensures \result >= 0;
  ensures \result == (a >= 0 ? (long)a : -(long)a);
*/
long spec_abs1(int a)
{
   long abs;
   abs = a;
   if (a < 0) {
      abs = -abs;
   }
   return abs;
}
#ifdef OUT_OF_TASK
#include <stdio.h>
int main(void)
{
   int a = spec_abs1(SPEC_INT_MIN+1);
   //@ assert a == SPEC_INT_MAX;
}
#endif
