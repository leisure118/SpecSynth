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
  while (x > 0) {
    x--;
    y--;
    z++;
    z++;
  }
  //@ assert(z<=0);
  return 0;
}
