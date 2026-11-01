int main() {
  int x = -5000;
  int y = 0;
  
  /*@
    loop invariant y >= 0;
    loop invariant (y == 0) ==> (x == -5000);
    loop assigns x, y;
    loop variant (y == 0 ? 1 : 0) - x;
  */
  while ((x < 0)) {
    x  = x + y;
    y  = y + 1;
  }
  // post-condition
  //@ assert(y > 0);
}
