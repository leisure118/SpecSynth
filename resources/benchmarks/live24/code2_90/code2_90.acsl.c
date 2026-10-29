void foo(int x) {
  int lock = 0;
  int y = x + 1;
  /*@
    loop invariant lock == 0 || lock == 1;
    loop invariant lock == 0 || x == y;
    loop invariant lock == 1 || y == x + 1;
    loop assigns lock, x, y;
    loop variant 2147483647 - x;
  */
  while (x != y) {
    if (unknown()) {
      lock = 1;
      x  = y;
    } else {
      lock = 0;
      x  = y;
      y  = y + 1;
    }
  }
  //@ assert lock == 1;
}