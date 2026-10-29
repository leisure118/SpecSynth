/*@ axiomatic Factorial {
    logic integer factorial(integer i);
    axiom nil:
       factorial(0) == 1;
    axiom step:
       \forall integer i; i >= 0 ==>
          factorial(i) == factorial(i - 1) * i;
    lemma non_negative:
       \forall integer i; i >= 0 ==>
          factorial(i) > 0;
    }
 */
#define SPEC_ULONG_MAX 18446744073709551615UL
/*@
  ensures \result == factorial(i);
  assigns \nothing;
*/
unsigned long factorial(unsigned i)
{
   unsigned long f = 1;
   /*@
     loop invariant i <= \at(i, Pre);
     loop invariant factorial(\at(i, Pre)) == f * factorial(i);
     loop assigns f, i;
     loop variant i;
   */
   while (i) {
      f *= i--;
   }
   return f;
}
#ifdef OUT_OF_TASK
#include <stdio.h>
int main(void)
{
   int a = factorial(5);
   int b = factorial(0);
   //@ assert a == 120;
   //@ assert b == 1;
}
#endif