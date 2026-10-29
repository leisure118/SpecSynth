/*@
requires (x == 100);
*/
void foo(int x) { 
  // loop body
  /*@
    loop invariant x >= 0;
    loop assigns x;
    loop variant x;
  */
  while (x > 0) {
    x  = x - 1;
  }
  // post-condition
  //@ assert(x == 0);
}
