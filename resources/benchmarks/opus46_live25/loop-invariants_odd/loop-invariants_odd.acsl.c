#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();

/*@ axiomatic BitAdd {
    axiom lsb_add2: \forall integer x; (x & 1) == 1 ==> ((x + 2) & 1) == 1;
}*/

int main(void) {
  unsigned int x = 1;
  /*@
    loop invariant (x & 1) == 1;
    loop assigns x;
  */
  while (unknown()) {
    x += 2;
  }
  //@ assert(x % 2);
  return 0;
}
