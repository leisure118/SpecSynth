void main() {
  // variable declarations
  int x;
  int y;
  // pre-conditions
  x = 1;
  y = 0;
  // loop body
  /*@
    loop invariant 0 <= y <= 1000;
    loop invariant x == 1 + y * (y - 1) / 2;
    loop assigns x, y;
    loop variant 1000 - y;
  */
  while (y < 1000) {
    x  = (x + y);
    y  = (y + 1);
  }
  // post-condition
  //@ assert(x >= y);
}
