void main() {
  int x;
  int y;
  x = 1;
  y = 0;
  /*@
    loop invariant 0 <= y <= 100000;
    loop invariant x >= 1;
    loop invariant x >= y;
    loop assigns x, y;
    loop variant 100000 - y;
  */
  while (y < 100000) {
    x  = x + y;
    y  = y + 1;
  }
  //@ assert  (x >= y) ;
}