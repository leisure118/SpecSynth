int main()
{
  unsigned int i = 0;
  unsigned int j = 0;
  unsigned int k = 0;
  /*@
    loop invariant k == 3 * i;
    loop invariant j == 2 * i;
    loop invariant k <= 0x0fffffff;
    loop assigns i, j, k;
    loop variant 0x0fffffff - k;
  */
  while (k < 0x0fffffff) {
    i = i + 1;
    j = j + 2;
    k = k + 3;
    //@assert((k == 3*i) && (j == 2*i));
  }
}
