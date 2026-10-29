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
  if (!(x<y)) return 0;
  /*@
    loop invariant x <= y + 99;
    loop assigns x;
    loop variant y - x;
  */
  while (x<y) {
    x=x+100;
  }
  //@ assert(x >= y && x <= y + 99);
  return 0;
}
