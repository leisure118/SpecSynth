/*@
requires (x == 10000);
*/
void foo(int x) {
  /*@
    loop invariant x >= 0;
    loop assigns x;
    loop variant x;
  */
  while ((x > 0)) {
    (x  = (x - 1));
  }
  //@ assert  (x == 0) ;
}