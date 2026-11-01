/*@
  requires z < 0x0fffffff;
  assigns \nothing;
  ensures \result == z + 2;
*/
unsigned int f(unsigned int z) {
  return z + 2;
}
int main(void) {
  unsigned int x = 0;
  /*@
    loop invariant x % 2 == 0;
    loop assigns x;
    loop variant 0x0fffffff - x;
  */
  while (x < 0x0fffffff) {
    x = f(x);
  }
  //@assert(!(x % 2));
}
