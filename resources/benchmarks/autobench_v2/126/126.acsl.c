void foo(int x, int y) {
  int i = x;
  int j = y;

  /*@
    loop invariant x - y == i - j;
    loop assigns x, y;
  */
  while (x != 0) {
    x  = x - 1;
    y  = y - 1;
  }
  // post-condition
  if (i == j) {
    //@ assert(y == 0);
  }
}
