/*@
  requires 0 <= x <= 10;
  requires 0 <= y <= 10;
*/
void foo(int x, int y) {
  int z1;
  int z2;
  int z3;
  /*@
    loop invariant x - y == \at(x - y, LoopEntry);
    loop assigns x, y;
  */
  while (unknown()) {
    x  = x + 10;
    y  = y + 10;
  }
  if (y == 0) {
    //@ assert x != 20;
  }
}