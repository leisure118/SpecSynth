int main() {
  int x = 0;
  /*@
    loop invariant 0 <= x <= 100;
    loop assigns x;
    loop variant 100 - x;
  */
  while (x < 100) {
    x = x + 1;
  }
  //@ assert x == 100;
}