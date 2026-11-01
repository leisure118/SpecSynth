#include <assert.h>
int unknown1();
int unknown2();
int unknown3();
int unknown4();


/*
 * From CAV'12 by Sharma et al.
 */

void main() {
  int x = 0;
  int y = 0;
  int n = 0;
  /*@
    loop invariant x == y;
    loop invariant x >= 0;
    loop invariant n == 0;
    loop assigns x, y;
  */
  while(unknown()) {
      x++;
      y++;
  }
  /*@
    loop invariant x == y;
    loop invariant x >= 0;
    loop invariant n == 0;
    loop assigns x, y;
    loop variant x;
  */
  while(x!=n) {
      x--;
      y--;
  }
  //@ assert(y==n);
}
