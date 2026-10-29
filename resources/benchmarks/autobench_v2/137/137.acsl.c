#include <assert.h>
int unknown1();
int unknown2();
int unknown3();
int unknown4();


void main() {
  int x, y;

  x = -50;
  /*@
    loop invariant x < 0 || y > 0;
    loop assigns x, y;
    loop variant 2147483647 - y;
  */
  while( x < 0 ) {
	x = x + y;
	y++;
  }
  //@ assert(y > 0);
}

