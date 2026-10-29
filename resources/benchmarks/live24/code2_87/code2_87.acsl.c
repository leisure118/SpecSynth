void foo(int x, int y) {
  int lock = 1;
  /*@
    loop invariant lock == 1 || x != y;
    loop assigns lock, x, y;
  */
  while ((x != y)) {
      if (unknown()) {
        lock  = 1;
        x = y;
      } else {
        lock = 0;
        x = y;
        y = y + 1;
      }
  }
  //@ assert lock == 1;
}