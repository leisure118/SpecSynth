#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
int main(void) {
  unsigned int s = 0;
  while (unknown()) {
    if (s != 0) {
      ++s;
    }
    if (unknown()) {
      //@ assert(s == 0);
    }
  }
  return 0;
}
