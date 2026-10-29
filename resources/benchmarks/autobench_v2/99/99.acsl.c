/*@
requires n >= 0;
*/
void foo(int n) {
  int x = n;
  int y = 0;
  
  /*@
    loop invariant 0 <= x <= n;
    loop invariant n == x + y;
    loop assigns x, y;
    loop variant x;
  */
  while (x > 0) {
    y  = y + 1;
    x  = x - 1;
  }
  // post-condition
  //@ assert(n == x + y);
}
