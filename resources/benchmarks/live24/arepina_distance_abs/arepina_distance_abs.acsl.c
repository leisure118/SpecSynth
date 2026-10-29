#define SPEC_INT_MIN -2147483648
#define SPEC_INT_MAX 2147483647
/*@
  requires a != SPEC_INT_MIN && b != SPEC_INT_MIN;
  assigns \nothing;
  ensures \result == \abs(\abs(a) - \abs(b));
*/
unsigned distance_abs(int a, int b)
{
   unsigned ua = a < 0 ? -a : a;
   unsigned ub = b < 0 ? -b : b;
   return ua > ub ? ua - ub : ub - ua;
}
#include <stdio.h>
int main(void)
{
   int a = distance_abs(3, 30);
   int b = distance_abs(-5, -20);
   int c = distance_abs(7, -10);
   int d = distance_abs(-2, 15);
   //@ assert a == 27;
   //@ assert b == 15;
   //@ assert c == 17;
   //@ assert d == 17;
   return 0;
}
