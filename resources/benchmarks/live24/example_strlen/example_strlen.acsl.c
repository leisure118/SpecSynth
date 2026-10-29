int main() {
  int s[6] = {104, 101, 108, 108, 111, 0};
  int i = 0;
  /*@
    loop invariant 0 <= i <= 5;
    loop invariant \forall integer j; 0 <= j < i ==> s[j] != 0;
    loop assigns i;
    loop variant 5 - i;
  */
  while (s[i] != 0) {
    i++;
  }
  //@ assert(i == 5);
  return 0;
}
