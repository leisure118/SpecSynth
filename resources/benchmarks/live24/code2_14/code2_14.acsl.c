/*@
  requires 0 <= x <= 2;
  requires 0 <= y <= 2;
*/
void foo(int x, int y) {
  int z1;
  int z2;
  int z3;
  /*@
    loop invariant \at(x, LoopEntry) - \at(y, LoopEntry) == x - y;
    loop assigns x, y;
  */
  while (unknown()) {
    x  = x + 2;
    y  = y + 2;
  }
  if (y == 0) {
    //@ assert x != 4;
  }
}