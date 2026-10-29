#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
int main(void) {
  unsigned int x = 1;
  while (unknown()) {
    x += 2;
  }
  //@ assert(x % 2);
  return 0;
}
