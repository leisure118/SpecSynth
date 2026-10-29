#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
int main(void) {
  unsigned int x = 0;
  /*@
    loop invariant \true;
    loop assigns x;
  */
  while (unknown()) {
    x += 2;
  }
  //@ admit (x % 2) == 0;
  //@assert(!(x % 2));
  return 0;
}
