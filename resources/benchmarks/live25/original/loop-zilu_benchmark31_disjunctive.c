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
  if (!(x < 0)) return 0;
  while (1) {
    if (x>=0) {
      break;
    } else {
      x=x+y; y++;
    }
  }
  //@ assert(y>=0);
  return 0;
}
