int main(void) {
  unsigned int x = 0;
  /*@
    loop invariant (x >= 0xfff0) ==> (x % 2 == 0);
    loop assigns x;
    loop variant 0x0fffffff - x;
  */
  while (x < 0x0fffffff) {
    if (x < 0xfff0) {
      x++;
    } else {
      x += 2;
    }
  }
  //@assert(!(x % 2));
}
