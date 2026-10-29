/*@
  requires \valid_read(a + (0 .. n-1));
  requires n >= 0;
  ensures \result == 1 <==> (\exists integer k; 0 <= k < n && a[k] == x);
  ensures \result == 0 <==> (\forall integer k; 0 <= k < n ==> a[k] != x);
  assigns \nothing;
*/
int arraysearch(int* a, int x, int n) { 

  /*@
    loop invariant 0 <= p <= n;
    loop invariant \forall integer k; 0 <= k < p ==> a[k] != x;
    loop assigns p;
    loop variant n - p;
  */
  for (int p = 0; p < n; p++) {
    // STart
    if (x == a[p]) 
       return 1;
    // End
  }
  return 0;
}

// write a test
void main() {
  int arr[5] = {1, 2, 3, 4, 5};
  int sum = arraysearch(arr, 3, 5);
  //@ assert sum == 1;
}