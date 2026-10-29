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
  if (!(x==1 && y==0)) return 0;
  /*@
    loop invariant x >= 1;
    loop invariant y >= 0;
    loop invariant x >= y;
    loop assigns x, y;
  */
  while (unknown()) {
    x=x+y;
    y++;
  }
  //@ assert(x >= y);
  return 0;
}
