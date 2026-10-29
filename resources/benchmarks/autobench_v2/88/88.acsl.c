void foo(int x) {
  int lock = 0;
  int y = x + 1;

  /*@
    loop invariant x <= y;
    loop invariant (x == y) ==> (lock == 1);
    loop assigns x, y, lock;
    loop variant 2147483647 - x;
  */
  while (x != y) {
    if (unknown()) {
      lock = 1;
      x = y;
    } else {
      lock = 0;
      x = y;
      y = y + 1;
    }
  }
  // post-condition
  //@ assert(lock == 1);
}
