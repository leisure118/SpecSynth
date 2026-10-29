/*@
  requires 0 <= x <= 2;
  requires 0 <= y <= 2;
*/
void foo(int x, int y) {
  // loop body
  /*@
    loop invariant x - y == \at(x, LoopEntry) - \at(y, LoopEntry);
    loop invariant 0 <= y;
    loop assigns x, y;
  */
  while (unknown()) {
    x  = x + 2;
    y  = y + 2;
  }
  // post-condition
  if (y == 0) {
    //@ assert(x != 4);
  }
}
