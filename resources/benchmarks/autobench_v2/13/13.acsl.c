/*@
  requires 0 <= x <= 2;
  requires 0 <= y <= 2;
*/
void foo(int x, int y) {
  // loop body
  /*@
    loop invariant x - y == \at(x - y, LoopEntry);
    loop assigns x, y;
    loop variant 2147483647 - x;
  */
  while (unknown()) {
    x  = x + 2;
    y  = y + 2;
  }
  // post-condition
  if (x == 4) {
    //@ assert(y != 0);
  }
}
