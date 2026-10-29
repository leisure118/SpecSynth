#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
int main(void) {
  int w = unknown();
  int x = w;
  int y = w + 1;
  int z = x + 1;
  /*@
    loop invariant y == z;
    loop assigns y, z;
    loop variant (0x7FFFFFFF - y);
  */
  while (unknown()) {
    y++;
    z++;
  }
  //@ assert(y == z);
  return 0;
}
