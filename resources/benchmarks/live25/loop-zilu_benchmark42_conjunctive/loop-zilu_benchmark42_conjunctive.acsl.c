#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include <assert.h>
int main() {
  int x = unknown();
  int y = unknown();
  int z = unknown();
  if (!(x == y && x >= 0 && x+y+z==0)) return 0;
  /*@
    loop invariant x >= 0;
    loop invariant x == y;
    loop invariant 2*x + z == 0;
    loop assigns x, y, z;
    loop variant x;
  */
  while (x > 0) {
    x--;
    y--;
    z++;
    z++;
  }
  //@ assert(z<=0);
  return 0;
}
