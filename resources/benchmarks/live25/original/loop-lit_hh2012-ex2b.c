# include <limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include <assert.h>
int main() {
  int n = 0;
  while (1) {
    //@ assert(n <= 60);
    if (unknown()) {
      if (n < 60) {
        n++;
      }
      else {
        //@ assert(n == 60);
        n = 0;
      }
    }
  }
  return 0;
}
