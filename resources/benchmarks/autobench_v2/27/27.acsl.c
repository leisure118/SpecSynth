/*@
requires x == n;
requires n >= 1;
*/
void foo(int x, int n) {
  // loop body
  /*@
    loop invariant x >= 1;
    loop assigns x;
    loop variant x - 1;
  */
  while (x > 1) {
    x  = x - 1;
  }
  // post-condition
  if (n >= 0) {
    //@ assert(x == 1);
  }
}