int main() {
  int N = 10;
  int fib[10];
  fib[0] = 0;
  fib[1] = 1;
  int i;
  /*@
    loop invariant 2 <= i <= N;
    loop invariant \forall integer j; 0 <= j < 2 ==> fib[j] == j;
    loop invariant \forall integer j; 2 <= j < i ==> fib[j] == fib[j-1] + fib[j-2];
    loop assigns i, fib[2 .. N-1];
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
