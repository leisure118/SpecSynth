int main(void) {
  unsigned int x = 0;
  unsigned int y = 1;
  /*@
    loop invariant 0 <= x <= 6;
    loop invariant (x == 0 ==> y == 1) && (x == 1 ==> y == 2) && (x == 2 ==> y == 4) && (x == 3 ==> y == 8) && (x == 4 ==> y == 16) && (x == 5 ==> y == 32) && (x == 6 ==> y == 64);
    loop assigns x, y;
    loop variant 6 - x;
  */
  while (x < 6) {
    x++;
    y *= 2;
  }
  //@ assert(y % 3);
}
