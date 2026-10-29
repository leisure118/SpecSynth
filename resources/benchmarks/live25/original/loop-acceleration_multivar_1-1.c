#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
int main(void) {
  int x = unknown();
  int y = x;
  while (x < 1024) {
    x++;
    y++;
  }
  //@ assert(x == y);
}
