int main(void) {
  unsigned int x = 0;
  unsigned int y = 1;
  /*@
    loop invariant 0 <= x <= 6;
    loop invariant y == 1 << x;
    loop assigns x, y;
    loop variant 6 - x;
  */
  while (x < 6) {
    x++;
    y *= 2;
  }
  //@ assert(y % 3);
}
