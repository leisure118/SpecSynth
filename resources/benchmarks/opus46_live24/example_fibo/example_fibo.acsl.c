int main() {
  int N = 10;
  int fib[10];
  fib[0] = 0;
  fib[1] = 1;
  int i;
  /*@
    loop invariant 2 <= i <= N;
    loop invariant fib[0] == 0;
    loop invariant fib[1] == 1;
    loop invariant i >= 3 ==> fib[2] == 1;
    loop invariant i >= 4 ==> fib[3] == 2;
    loop invariant i >= 5 ==> fib[4] == 3;
    loop invariant i >= 6 ==> fib[5] == 5;
    loop invariant i >= 7 ==> fib[6] == 8;
    loop invariant i >= 8 ==> fib[7] == 13;
    loop invariant i >= 9 ==> fib[8] == 21;
    loop invariant i >= 10 ==> fib[9] == 34;
    loop assigns i, fib[2 .. 9];
    loop variant N - i;
  */
  for (i = 2; i < N; i++) {
    fib[i] = fib[i-1] + fib[i-2];
  }
  //@ assert(fib[0] == 0);
  //@ assert(fib[1] == 1);
  //@ assert(fib[9] == 34);
  return 0;
}
