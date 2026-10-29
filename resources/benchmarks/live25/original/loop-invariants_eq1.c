#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
int main(void) {
  int w = unknown();
  int x = w;
  int y = unknown();
  int z = y;
  while (unknown()) {
    if (unknown()) {
      ++w; ++x;
    } else {
      --y; --z;
    }
  }
  //@ assert(w == x && y == z);
  return 0;
}
