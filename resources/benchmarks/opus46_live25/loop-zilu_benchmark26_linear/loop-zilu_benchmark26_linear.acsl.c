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
    loop invariant x <= y;
    loop assigns x;
    loop variant y - x;
  */
  while (x<y) {
    x=x+1;
  }
  //@ assert(x==y);
  return 0;
}
