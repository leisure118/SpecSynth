int arraymax(int* a, int n) {
  int i = 1;
  int max = a[0];
  while (i < n) {
    if (max < a[i])
    max = a[i];
    i = i + 1;
  }
  //@ assert \forall integer k;  0 <= k < n ==> max >=  a[k];
  return max;
}  