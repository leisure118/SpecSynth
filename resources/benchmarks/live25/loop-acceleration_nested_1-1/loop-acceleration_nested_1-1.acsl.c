int main(void) {
  unsigned int x = 0;
  unsigned int y = 0;
  /*@
    loop invariant 0 <= x <= 0x0fffffff;
    loop assigns x, y;
    loop variant 0x0fffffff - x;
  */
  while (x < 0x0fffffff) {
    y = 0;
    /*@
      loop invariant 0 <= y <= 10;
      loop assigns y;
      loop variant 10 - y;
    */
    while (y < 10) {
      y++;
    }
    x++;
  }
  //@ assert(x % 2);
}
