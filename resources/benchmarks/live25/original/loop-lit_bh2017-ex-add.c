#include <limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include <assert.h>
int main() {
  int m = 0;
  int n = 0;
  while (1) {
    //@ assert(m <= 60);
    //@ assert(n <= 60);
    if (unknown()) {
      if (unknown()) {
        if (m < 60) {
          m++;
        }
        else {
          //@ assert(m == 60);
          m = 0;
        }
      }
    }
    if (unknown()) {
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
  }
  return 0;
}
