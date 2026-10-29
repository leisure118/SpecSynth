void foo(int n) {
  int x = 0;

  /*@
    loop invariant 0 <= x && (x <= n || n < 0);
    loop assigns x;
    loop variant n - x;
  */
  while (x < n) {
    x = x + 1;
  }
  // post-condition
  if (x != n) {
    //@ assert(n < 0);
  }
}
