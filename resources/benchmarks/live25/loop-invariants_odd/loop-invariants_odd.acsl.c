#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();

/*@
  lemma add2_lsb: \forall unsigned int u; (u & 1) == ((u + 2) & 1);
*/

int main(void) {
  unsigned int x = 1;
  /*@
    loop invariant (x & 1) == 1;
    loop assigns x;
    loop variant 0;
  */
  while (unknown()) {
    x += 2;
  }
  //@ assert(x % 2);
  return 0;
}
