extern int unknown(void);
/*@
  requires 0 <= x <= 10;
  requires 0 <= y <= 10;
*/
void foo(int x, int y) {
  // loop body
  /*@
    loop invariant x - y == \at(x, LoopEntry) - \at(y, LoopEntry);
    loop invariant \at(x, LoopEntry) <= 10;
    loop invariant \at(y, LoopEntry) >= 0;
    loop assigns x, y;
  */
  while (unknown()) {
    x  = x + 10;
    y  = y + 10;
  }
  // post-condition
  if (x == 20) {
    //@ assert(y != 0);
  }
}
