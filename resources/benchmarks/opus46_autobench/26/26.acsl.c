/*@
requires x == n;
requires x != 1;
*/
void foo(int x, int n) {
  // loop body
  /*@
    loop invariant (n > 1) ==> (1 <= x <= n);
    loop invariant (n <= 1) ==> (x == n);
    loop assigns x;
    loop variant x - 1;
  */
  while (x > 1) {
    x  = x - 1;
  }
  // post-condition
  if (x != 1) {
    //@ assert(n < 1);
  }
}
