int main() {
  int x = -15000;
  int y = 0;
  /*@
    loop invariant 0 <= y;
    loop invariant x == -15000 + y*(y-1)/2;
    loop assigns x, y;
    loop variant -x - y + 51;
  */
  while (x < 0) {
    x  = x + y;
    y  = y + 1;
  }
  //@ assert y > 0;
}