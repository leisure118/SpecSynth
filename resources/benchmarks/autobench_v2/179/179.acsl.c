#include <assert.h>

int unknown1();
int unknown2();
int unknown3();
int unknown4();

int main() {

  int w = 1;
  int z = 0;
  int x = 0;
  int y = 0;

  /*@
    loop invariant (x == 0 && w == 1) || (x == 1 && w == 2);
    loop invariant (y == 0 && z == 0) || (y == 1 && z == 1);
    loop assigns w, z, x, y;
  */
  while (unknown2()) {
    if (w % 2 == 1) {
      x++;
      w++;
    }
    if (z % 2 == 0) {
      y++;
      z++;
    }
  }

  //@ assert(x <= 1);
  return 0;
}