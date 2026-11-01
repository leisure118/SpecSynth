int main() {
  int x = -15000;
  int y = 0;
  /*@
    loop invariant y >= 0;
    loop invariant x < 0 || y > 0;
    loop assigns x, y;
    loop variant (-x) + (y == 0 ? 1 : 0);
  */
  while (x < 0) {
    x  = x + y;
    y  = y + 1;
  }
  //@ assert y > 0;
}