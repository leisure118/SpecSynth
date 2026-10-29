void foo(int y) {
  int x = 1;
  /*@
    loop invariant x >= 1;
    loop assigns x;
    loop variant y - x;
  */
  while (x < y) {
    x = x + x;
  }
  //@ assert x >= 1;
}