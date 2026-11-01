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
  if (!(y == x)) return 0;
  /*@
    loop invariant x == y;
    loop assigns x, y;
  */
  while (unknown()) {
    x++;
    y++;
  }
  //@ assert(x == y);
  return 0;
}
