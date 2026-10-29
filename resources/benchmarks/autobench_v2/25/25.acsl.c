/*@
requires (x == 10000);
*/
void foo(int x) {
  // loop body
  /*@
    loop invariant 0 <= x <= 10000;
    loop assigns x;
    loop variant x;
  */
  while ((x > 0)) {
    (x  = (x - 1));
  }
  // post-condition
  //@ assert( (x == 0) );
}
