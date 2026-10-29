/*@
requires n >= 1;
*/
void foo(int n) {
  int x = n;
  // loop body
  /*@
    loop invariant 1 <= x <= n;
    loop assigns x;
    loop variant x;
  */
  while (x > 1) {
    x  = x - 1;
  }
  // post-condition
  if (n >= 0) {
    //@ assert(x == 1);
  }
}
