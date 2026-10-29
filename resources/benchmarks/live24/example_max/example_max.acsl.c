int main() {
  int N = 10;
  int arr[10] = {3, 1, 4, 1, 5, 9, 2, 6, 5, 3};
  int max = arr[0];
  int i;
  /*@
    loop invariant 1 <= i <= N;
    loop invariant \forall integer j; 0 <= j < i ==> max >= arr[j];
    loop invariant \exists integer k; 0 <= k < i && max == arr[k];
    loop assigns i, max;
    loop variant N - i;
  */
  for (i = 1; i < N; i++) {
    if (arr[i] > max) {
      max = arr[i];
    }
  }
  //@ assert(max == 9);
  return 0;
}
