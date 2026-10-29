#include <assert.h>

int unknown1();
int unknown2();
int unknown3();
int unknown4();

void main() {
  int w = 1, z = 0, x = 0, y = 0;
  /*@
    loop invariant x == y;
    loop invariant x >= 0;
    loop invariant w % 2 == 1;
    loop invariant z % 2 == 0;
    loop assigns x, y, w, z;
  */
  while (unknown1()) {
    /*@
      loop invariant x == y;
      loop invariant x >= 0;
      loop invariant w % 2 == 1;
      loop invariant z % 2 == 0;
      loop assigns x, y;
    */
    while (unknown2()) {
      if (w % 2 == 1)
        x++;
      if (z % 2 == 0)
        y++;
    }
    /*@
      loop invariant x == y;
      loop invariant x >= 0;
      loop invariant w % 2 == 1;
      loop invariant z % 2 == 0;
      loop assigns w, z;
    */
    while (unknown4()) {
      z = x + y;
      w = z + 1;
    }
  }
  //@ assert(x == y);
}