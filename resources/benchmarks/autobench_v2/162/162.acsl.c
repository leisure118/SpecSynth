int unknown1();
int unknown2();
int unknown3();

void main() {
  int a = 1;
  int b = 1;
  int c = 2;
  int d = 2;
  int x = 3;
  int y = 3;
  /*@
    loop invariant a + c == b + d;
    loop assigns a, b, c, d, x, y;
  */
  while (unknown1()) {
    x = a + c;
    y = b + d;
    if ((x + y) % 2 == 0) {
      a++;
      d++;
    } else {
      a--;
    }

    /*@
      loop invariant a + c == b + d;
      loop assigns b, c;
    */
    while (unknown2()) {
      c--;
      b--;
    }
  }
  //@ assert(a + c == b + d);
}