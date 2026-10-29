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
  if (!(y>0 || x>0 || z>0)) return 0;
  while (unknown()) {
    if (x>0) {
      x++;
    }
    if (y>0) {
      y++;
    } else {
      z++;
    }
  }
  //@ assert(x>0 || y>0 || z>0);
  return 0;
}
