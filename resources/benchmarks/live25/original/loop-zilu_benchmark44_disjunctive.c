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
  while (x<y) {
    if ((x<0 && y<0)) {
      x=x+7; y=y-10;
    }
    if ((x<0 && y>=0)) {
      x=x+7; y=y+3;
    } else {
      x=x+10; y=y+3;
    }
  }
  //@ assert(x >= y && x <= y + 16);
  return 0;
}
