#include <assert.h>

int unknown1();
int unknown2();
int unknown3();
int unknown4();

void foo(int flag) {
  int x = 0;
  int y = 0;
  int j = 0;
  int i = 0;

  /*@
    loop invariant 0 <= x;
    loop invariant x == y;
    loop invariant i <= j;
    loop assigns x, y, i, j;
  */
  while (unknown1()) {
    x++;
    y++;
    i += x;
    j += y;
    if (flag) {
      j += 1;
    }
  }
  if (j >= i)
    x = y;
  else
    x = y + 1;

  int w = 1;
  int z = 0;
  /*@
    loop invariant 0 <= x;
    loop invariant 0 <= y;
    loop invariant 0 <= z;
    loop invariant x == y;
    loop invariant w - z == 1;
    loop assigns x, y, z, w;
  */
  while (unknown2()) {
    /*@
      loop invariant 0 <= x;
      loop invariant 0 <= y;
      loop invariant 0 <= z;
      loop invariant x == y;
      loop assigns x, y;
    */
    while (unknown3()) {
      if (w % 2 == 1)
        x++;
      if (z % 2 == 0)
        y++;
    }
    z = x + y;
    w = z + 1;
  }
  //@ assert(x == y);
}