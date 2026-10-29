int main() {
  int N = 10;
  int fib[10];
  fib[0] = 0;
  fib[1] = 1;
  int i;
  for (i = 2; i < N; i++) {
    fib[i] = fib[i-1] + fib[i-2];
  }
  //@ assert(fib[0] == 0);
  //@ assert(fib[1] == 1);
  //@ assert(fib[9] == 34);
  return 0;
}
