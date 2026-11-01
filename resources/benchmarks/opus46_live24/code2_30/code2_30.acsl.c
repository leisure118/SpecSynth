/*@
requires (x == 100);
*/
void foo(int x) { 
  /*@
    loop invariant 0 <= x <= 100;
    loop assigns x;
    loop variant x;
  */
  while (x > 0) {
    x  = x - 1;
  }
  //@ assert x == 0;
}