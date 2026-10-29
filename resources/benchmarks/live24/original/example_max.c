int main() {
  int N = 10;
  int arr[10] = {3, 1, 4, 1, 5, 9, 2, 6, 5, 3};
  int max = arr[0];
  int i;
  for (i = 1; i < N; i++) {
    if (arr[i] > max) {
      max = arr[i];
    }
  }
  //@ assert(max == 9);
  return 0;
}
