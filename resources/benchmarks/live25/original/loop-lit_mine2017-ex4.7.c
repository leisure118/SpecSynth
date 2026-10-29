#include <limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include <assert.h>
int main() {
  int x = 0;
  while (unknown() == 0) {
    //@ assert(0 <= x);
    //@ assert(x <= 40);
    if (unknown() == 0) {
      x++;
      if (x > 40)
        x = 0;
    }
  }
  return 0;
}
