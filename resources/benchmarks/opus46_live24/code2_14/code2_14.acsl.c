extern int unknown(void);

/*@
  requires 0 <= x <= 2;
  requires 0 <= y <= 2;
*/
void foo(int x, int y) {
  int z1;
  int z2;
  int z3;
  /*@
    loop invariant -2 <= x - y <= 2;
    loop invariant x >= 0;
    loop invariant y >= 0;
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
