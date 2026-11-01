int main() {
  int x = -50;
  int y = 0;

  /*@
    loop invariant y >= 0;
    loop invariant 2*x + 100 == y*y - y;
    loop assigns x, y;
    loop variant 100 - y*y;
  */
  while (x < 0) {
    x  = x + y;
    y  = y + 1;
  }
  // post-condition
  //@ assert(y > 0);
}
