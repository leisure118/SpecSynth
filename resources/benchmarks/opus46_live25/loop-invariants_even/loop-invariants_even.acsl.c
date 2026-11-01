#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();

/*@ axiomatic UintEven {
  axiom uint_mod2_even: \forall integer n; n % 2 == 0 ==> (unsigned int)n % 2 == 0;
} */

int main(void) {
  unsigned int x = 0;
  /*@
    loop invariant x % 2 == 0;
    loop assigns x;
  */
  while (unknown()) {
    x += 2;
  }
  //@assert(!(x % 2));
  return 0;
}
