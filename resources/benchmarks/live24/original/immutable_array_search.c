int arraysearch(int* a, int x, int n) { 
  for (int p = 0; p < n; p++) {
    if (x == a[p]) 
       return 1;
  }
  return 0;
}
void main() {
  int arr[5] = {1, 2, 3, 4, 5};
  int sum = arraysearch(arr, 3, 5);
  //@ assert sum == 1;
}