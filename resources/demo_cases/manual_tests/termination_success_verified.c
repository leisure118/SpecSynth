void main() {
  int x;
  int y;

  x = 1;
  y = 0;

  /*@
    loop invariant y <= x;
    loop invariant y <= 1000;
    loop invariant 2*x == 2 + y*(y - 1);
    loop invariant 1 <= x;
    loop invariant 0 <= y;
    loop assigns y;
    loop assigns x;
  */
  while (y < 1000) {
    x = x + y;
    y = y + 1;
  }

  //@ assert x >= y >= 1;
}
