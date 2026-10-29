#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
int main(void) {
  unsigned int x = 0;
  /*@
    loop invariant x % 4 == 0;
    loop assigns x;
  */
  while (unknown()) {
    x += 4;
    //@ admit x % 4 == 0;
  }
  //@ assert(!(x % 4));
  return 0;
}
