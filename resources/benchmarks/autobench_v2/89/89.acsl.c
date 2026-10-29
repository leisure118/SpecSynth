/*@
requires x == y;
*/
void foo(int x, int y) {
  int lock = 1;
  
  /*@
    loop invariant x == y || y == x + 1;
    loop invariant (x == y) ==> (lock == 1);
    loop invariant (y == x + 1) ==> (lock == 0);
    loop assigns x, y, lock;
  */
  while (x != y) {  
    if (unknown()) {
      lock = 1;
      x = y;
    } else {
      lock  = 0;
      x  = y;
      y  = y + 1; 
    }
  }
  // post-condition
  //@ assert(lock == 1);
}
