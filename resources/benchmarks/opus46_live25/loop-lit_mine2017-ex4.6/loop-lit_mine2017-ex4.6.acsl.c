#include <assert.h>
int main() {
  int x = 40;
  /*@
    loop invariant 0 <= x <= 40;
    loop assigns x;
    loop variant x;
  */
  while (x != 0) {
    //@ assert(x <= 40);
    x--;
    //@ assert(x >= 0);
  }
  //@ assert(x == 0);
  return 0;
}
