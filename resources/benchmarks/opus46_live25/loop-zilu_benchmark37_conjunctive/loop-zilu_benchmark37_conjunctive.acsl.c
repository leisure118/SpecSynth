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
  if (!(x == y && x >= 0)) return 0;
  /*@
    loop invariant x == y;
    loop invariant x >= 0;
    loop assigns x, y;
    loop variant x;
  */
  while (x > 0) {
    x--;
    y--;
  }
  //@ assert(y>=0);
  return 0;
}
