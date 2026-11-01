/*@ requires y <= 1073741824; */
void foo(int y) {
  int x = 1;
  
  /*@
    loop invariant 1 <= x;
    loop assigns x;
    loop variant y - x;
  */
  while (x < y) {
    x = x + x;
  }
  // post-condition
  //@ assert(x >= 1);
}
