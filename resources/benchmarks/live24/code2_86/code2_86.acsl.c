int main() {
  int x = -50;
  int y = 0;
  /*@
    loop invariant 0 <= y;
    loop invariant x == -50 + y*(y-1)/2;
    loop assigns x, y;
    loop variant 10 - y;
  */
  while (x < 0) {
    x  = x + y;
    y  = y + 1;
  }
  //@ assert y > 0;
}