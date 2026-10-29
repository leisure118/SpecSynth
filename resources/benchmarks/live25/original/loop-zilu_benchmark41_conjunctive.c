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
  if (!(x == y && y == 0 && z==0)) return 0;
  while (unknown()) {
    x++;y++;z-=2;
  }
  //@ assert(x == y && x >= 0 && x+y+z==0);
  return 0;
}
