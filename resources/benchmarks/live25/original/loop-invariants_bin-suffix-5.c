#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
int main(void) {
  unsigned int x = 5;
  while (unknown()) {
    x += 8;
  }
  //@assert((x & 5) == 5);
  return 0;
}
