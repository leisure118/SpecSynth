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
  if (!(y>0 || x>0)) return 0;
  /*@
    loop invariant x > 0 || y > 0;
    loop assigns x, y;
    loop variant INT_MAX - x + INT_MAX - y;
  */
  while (1) {
    if (x+y>-2) {
      break;
    }
    if (x>0) {
      x++;
    } else {
      y++;
    }
  }
  //@ assert(x>0 || y>0);
  return 0;
}
