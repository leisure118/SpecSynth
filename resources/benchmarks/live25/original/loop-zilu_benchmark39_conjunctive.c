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
  if (!(x == 4*y && x >= 0)) return 0;
  while (x > 0) {
    x-=4;
    y--;
  }
  //@ assert(y>=0);
  return 0;
}
