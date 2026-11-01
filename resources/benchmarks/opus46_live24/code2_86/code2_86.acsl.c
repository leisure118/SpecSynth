int main() {
  int x = -50;
  int y = 0;
  /*@
    loop invariant y >= 0;
    loop invariant 2*x == y*y - y - 100;
    loop assigns x, y;
    loop variant 100 - 2*x - y;
  */
  while (x < 0) {
    x  = x + y;
    y  = y + 1;
  }
  //@ assert y > 0;
}